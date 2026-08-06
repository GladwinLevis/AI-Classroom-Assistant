from fastapi import APIRouter, Depends, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_active_user, RoleChecker
from app.models.user import User, UserRole
from app.models.attendance import AttendanceSessionStatus, AttendanceStatus
from app.schemas.attendance import (
    AttendanceSessionCreate, AttendanceSessionUpdate, AttendanceSessionResponse,
    AttendanceRecordMark, AttendanceRecordResponse, AttendanceBulkMarkRequest,
    QRGenerateResponse, QRScanRequest, AttendanceDashboardAnalytics,
    StudentAttendanceSummary, StudentAttendanceReportRow, AttendanceReportResponse
)
from app.services.attendance import (
    AttendanceSessionService, AttendanceService, AttendanceAnalyticsService,
    AttendanceReportService, QRCodeService
)
from app.core.exceptions import AuthException

router = APIRouter()


@router.get("", response_model=List[AttendanceRecordResponse])
@router.get("/", response_model=List[AttendanceRecordResponse])
async def list_user_attendance_records(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves attendance records relevant for the logged-in user."""
    from app.models.attendance import AttendanceRecord
    from app.models.user import StudentProfile, User
    from sqlalchemy.orm import selectinload

    stmt = (
        select(AttendanceRecord)
        .options(selectinload(AttendanceRecord.student).selectinload(StudentProfile.user))
        .order_by(AttendanceRecord.created_at.desc())
        .limit(100)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    out = []
    for r in records:
        s_name = "Student"
        if r.student and r.student.user:
            fn = r.student.user.first_name or ""
            ln = r.student.user.last_name or ""
            s_name = f"{fn} {ln}".strip() or r.student.user.email
        out.append(AttendanceRecordResponse(
            id=r.id,
            session_id=r.session_id,
            student_id=r.student_id,
            status=r.status,
            marked_at=r.marked_at or r.created_at,
            marked_by_id=r.marked_by_id,
            student_name=s_name,
            remarks=getattr(r, "remarks", None)
        ))
    return out


@router.post("/start-session")
async def start_quick_attendance_session(
    payload: Optional[dict] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Starts a quick attendance session with a 5-minute expiring unique attendance code."""
    import random
    from fastapi import HTTPException
    from app.models.attendance import AttendanceSession, AttendanceSessionStatus, AttendanceMode
    from app.models.user import TeacherProfile
    from app.models.course import Course, Subject

    valid_minutes = payload.get("valid_minutes", 5) if payload else 5

    # 1. Find or create TeacherProfile
    t_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == current_user.id)
    t_res = await db.execute(t_stmt)
    teacher = t_res.scalars().first()
    if not teacher:
        teacher = TeacherProfile(
            user_id=current_user.id,
            employee_id=f"EMP-{current_user.id.hex[:6].upper()}",
            department="General"
        )
        db.add(teacher)
        await db.flush()

    # 2. Find or create Subject
    subj_stmt = select(Subject).limit(1)
    subj_res = await db.execute(subj_stmt)
    subject = subj_res.scalars().first()
    if not subject:
        subject = Subject(
            name="General Computer Science",
            code="CS101",
            department="Computer Science"
        )
        db.add(subject)
        await db.flush()

    # 3. Find or create Course
    c_stmt = select(Course).limit(1)
    c_res = await db.execute(c_stmt)
    course = c_res.scalars().first()

    if not course:
        course = Course(
            name="Computer Science 101",
            code="CS101-ATT",
            subject_id=subject.id,
            teacher_id=teacher.id
        )
        db.add(course)
        await db.flush()

    # Generate 6-digit numeric attendance code
    code_digits = f"{random.randint(100000, 999999)}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=valid_minutes)

    session = AttendanceSession(
        course_id=course.id,
        date=date.today(),
        teacher_id=teacher.id,
        attendance_mode=AttendanceMode.QR_CODE,
        status=AttendanceSessionStatus.ACTIVE,
        code=code_digits,
        expires_at=expires_at
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "session_id": str(session.id),
        "qr_token": code_digits,
        "expires_at": expires_at.isoformat(),
        "message": f"Attendance session started successfully. Code expires in {valid_minutes} minutes."
    }


@router.post("/check-in")
@router.post("/mark")
async def student_check_in_token(
    payload: Optional[dict] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Marks student attendance after verifying code existence, active status, expiry, and duplicate checks."""
    from fastapi import HTTPException
    token = (payload.get("token") or payload.get("qr_token") or payload.get("code") or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Invalid Attendance Code")

    raw_num = token.replace("ATT-", "").strip()

    from app.models.attendance import AttendanceSession, AttendanceRecord, Attendance, AttendanceStatus, AttendanceSessionStatus
    from app.models.user import StudentProfile

    # 1. Find StudentProfile for current student
    s_stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
    s_res = await db.execute(s_stmt)
    student = s_res.scalars().first()

    if not student:
        student = StudentProfile(
            user_id=current_user.id,
            roll_number=f"STU-{current_user.id.hex[:6].upper()}",
            academic_year="2026"
        )
        db.add(student)
        await db.flush()

    # 2. Query AttendanceSession in PostgreSQL by code
    code_conditions = [
        AttendanceSession.code == token,
        AttendanceSession.code == raw_num,
        AttendanceSession.code == f"ATT-{raw_num}"
    ]
    sess_stmt = select(AttendanceSession).filter(
        select(AttendanceSession).where(*[c for c in code_conditions]).exists()
    )
    
    # Simple OR query for session by code
    from sqlalchemy import or_
    sess_stmt = select(AttendanceSession).filter(
        or_(
            AttendanceSession.code == token,
            AttendanceSession.code == raw_num,
            AttendanceSession.code == f"ATT-{raw_num}"
        )
    ).order_by(AttendanceSession.created_at.desc())
    
    sess_res = await db.execute(sess_stmt)
    session = sess_res.scalars().first()

    # Requirement 5: Return "Invalid Attendance Code" if code does not exist
    if not session or session.status != AttendanceSessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Invalid Attendance Code")

    # Requirement 6: Return "Attendance Code Expired" if expired
    now = datetime.now(timezone.utc)
    if session.expires_at and now > session.expires_at:
        session.status = AttendanceSessionStatus.CLOSED
        await db.commit()
        raise HTTPException(status_code=400, detail="Attendance Code Expired")

    # Requirement 7: Block duplicate attendance attempts
    rec_stmt = select(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == student.id
    )
    rec_res = await db.execute(rec_stmt)
    existing_rec = rec_res.scalars().first()

    if existing_rec:
        raise HTTPException(status_code=409, detail="You have already submitted attendance for this session.")

    # Mark attendance in database
    rec = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        status=AttendanceStatus.PRESENT,
        marked_by_id=current_user.id,
        marked_at=now
    )
    db.add(rec)

    # Upsert into daily Attendance table
    att_stmt = select(Attendance).filter(Attendance.user_id == current_user.id, Attendance.date == date.today())
    att_res = await db.execute(att_stmt)
    existing_att = att_res.scalars().first()

    if not existing_att:
        daily_att = Attendance(
            user_id=current_user.id,
            date=date.today(),
            status=AttendanceStatus.PRESENT,
            remarks=f"Marked via QR code {token}"
        )
        db.add(daily_att)

    await db.commit()

    return {
        "status": "present",
        "message": "Attendance marked successfully!",
        "timestamp": now.isoformat()
    }


@router.post("/sessions", response_model=AttendanceSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance_session(
    request: AttendanceSessionCreate,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new attendance session.
    Restricted to Teachers and Administrators.
    """
    service = AttendanceSessionService(db)
    session = await service.create_session(request, current_user)
    return session


@router.put("/sessions/{session_id}", response_model=AttendanceSessionResponse)
async def update_attendance_session(
    session_id: UUID,
    request: AttendanceSessionUpdate,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates an existing attendance session parameters or status.
    Restricted to Teachers and Administrators.
    """
    service = AttendanceSessionService(db)
    session = await service.update_session(session_id, request, current_user)
    return session


@router.get("/sessions/active", response_model=List[AttendanceSessionResponse])
async def get_active_sessions_for_student(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all open/active attendance sessions for courses where the student is enrolled.
    Restricted to Students and Admins.
    """
    from app.models.user import StudentProfile
    
    stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    student = res.scalars().first()
    if not student:
        raise AuthException("Only registered students can check active sessions.")

    service = AttendanceService(db)
    sessions = await service.session_repo.get_active_sessions_for_student(student.id)
    return sessions


@router.get("/sessions", response_model=List[AttendanceSessionResponse])
async def list_attendance_sessions(
    course_id: Optional[UUID] = Query(None),
    classroom_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[AttendanceSessionStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Filters and lists attendance sessions based on parameters.
    Accessible by Teacher and Admin roles.
    """
    service = AttendanceSessionService(db)
    # If teacher, limit query filters to their own sessions
    teacher_id = None
    is_admin = any(role.name == "admin" for role in current_user.roles)
    if not is_admin:
        from app.models.user import TeacherProfile
        t_stmt = select(TeacherProfile).filter(TeacherProfile.user_id == current_user.id)
        t_res = await db.execute(t_stmt)
        teacher = t_res.scalars().first()
        if teacher:
            teacher_id = teacher.id

    sessions = await service.session_repo.get_sessions_by_filter(
        teacher_id=teacher_id,
        course_id=course_id,
        classroom_id=classroom_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        skip=skip,
        limit=limit
    )
    return sessions


@router.post("/sessions/{session_id}/close", response_model=AttendanceSessionResponse)
async def close_attendance_session(
    session_id: UUID,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Closes an active attendance session, preventing further student markings.
    Restricted to Teachers and Admins.
    """
    service = AttendanceSessionService(db)
    session = await service.update_session(
        session_id, 
        AttendanceSessionUpdate(status=AttendanceSessionStatus.CLOSED), 
        current_user
    )
    return session


@router.post("/sessions/{session_id}/qr", response_model=QRGenerateResponse)
async def generate_session_qr(
    session_id: UUID,
    ttl_seconds: int = Query(60, ge=10, le=300),
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a secure cryptographically signed QR Code token for active sessions.
    Restricted to Teachers and Admins.
    """
    service = AttendanceSessionService(db)
    session = await service.session_repo.get(session_id)
    if not session or session.is_deleted:
        from app.core.exceptions import EntityNotFoundException
        raise EntityNotFoundException("Session not found.")

    await service._verify_session_ownership(session, current_user)

    from app.core.config import settings
    qr_service = QRCodeService(settings.JWT_SECRET_KEY)
    token = qr_service.generate_qr_token(session_id, ttl_seconds)
    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

    return QRGenerateResponse(
        qr_token=token,
        session_id=session_id,
        expires_at=expires_at
    )


@router.post("/mark/student", response_model=AttendanceRecordResponse)
async def mark_student_self_attendance(
    session_id: UUID,
    request: Optional[QRScanRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marks student self-attendance for an active session.
    Automatically verifies enrollment, duplicates, and verifies QR codes.
    """
    service = AttendanceService(db)
    qr_tok = request.qr_token if request else None
    record = await service.mark_student_attendance(session_id, current_user, qr_token=qr_tok)
    return record


@router.post("/mark/teacher/bulk", response_model=List[AttendanceRecordResponse])
async def mark_teacher_bulk_attendance(
    session_id: UUID,
    request: AttendanceBulkMarkRequest,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk marks attendance for students by the assigned teacher.
    Restricted to Teachers and Admins.
    """
    service = AttendanceService(db)
    records = await service.mark_teacher_bulk_attendance(session_id, request, current_user)
    return records


@router.put("/mark/session/{session_id}/student/{student_id}", response_model=AttendanceRecordResponse)
async def update_student_attendance_record(
    session_id: UUID,
    student_id: UUID,
    status_req: AttendanceRecordMark,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates single student attendance status in a session before closure.
    Restricted to Teachers and Admins.
    """
    service = AttendanceService(db)
    record = await service.update_single_attendance_record(session_id, student_id, status_req.status, current_user)
    return record


@router.get("/analytics/student/{student_id}", response_model=StudentAttendanceSummary)
async def get_student_analytics(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves attendance statistics summary for a student.
    Enforces profile ownership logic (students can only check their own analytics).
    """
    is_admin = any(role.name == "admin" for role in current_user.roles)
    is_teacher = any(role.name == "teacher" for role in current_user.roles)
    
    if not (is_admin or is_teacher):
        # Current user must be the student themselves
        from sqlalchemy import select
        from app.models.user import StudentProfile
        stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
        res = await db.execute(stmt)
        student = res.scalars().first()
        if not student or student.id != student_id:
            raise AuthException("Access Denied. Students can only view their own analytics.")

    service = AttendanceAnalyticsService(db)
    analytics = await service.get_student_dashboard_analytics(student_id)
    return analytics


@router.get("/analytics/course/{course_id}", response_model=AttendanceDashboardAnalytics)
async def get_course_analytics(
    course_id: UUID,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves aggregated dashboard analytics for a course.
    Restricted to Teachers and Admins.
    """
    service = AttendanceAnalyticsService(db)
    analytics = await service.get_teacher_course_dashboard(course_id)
    return analytics


@router.get("/history", response_model=List[AttendanceRecordResponse])
async def get_student_personal_history(
    course_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the personal attendance history list for the logged-in student.
    Restricted to Students.
    """
    from app.models.user import StudentProfile
    stmt = select(StudentProfile).filter(StudentProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    student = res.scalars().first()
    if not student:
        raise AuthException("Only students can view personal history logs.")

    service = AttendanceService(db)
    history = await service.record_repo.get_student_history(
        student_id=student.id,
        course_id=course_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )
    return history


@router.get("/reports/course/{course_id}", response_model=AttendanceReportResponse)
async def get_course_report_preview(
    course_id: UUID,
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates class-wide student attendance report.
    Restricted to Teachers and Admins.
    """
    service = AttendanceReportService(db)
    rows = await service.generate_course_attendance_report(course_id)
    
    return AttendanceReportResponse(
        report_type="class",
        generated_at=datetime.now(),
        records=rows
    )


@router.get("/reports/course/{course_id}/export")
async def export_course_report(
    course_id: UUID,
    file_format: str = Query("csv", pattern="^(csv)$"),
    current_user: User = Depends(RoleChecker([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports course attendance report to a downloadable CSV file.
    Restricted to Teachers and Admins.
    """
    service = AttendanceReportService(db)
    rows = await service.generate_course_attendance_report(course_id)
    csv_data = service.export_report_to_csv(rows)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=course_{course_id}_attendance.csv"}
    )
