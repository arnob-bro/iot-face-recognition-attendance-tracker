"""
Report routes — daily, weekly, monthly, course-wise, and student-wise reports.
"""

from fastapi import APIRouter, Depends, Query, Response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
import csv
import io

from app.api.deps import require_teacher_or_admin
from app.schemas.auth import UserInToken
from app.schemas.report import (
    StudentAttendanceSummary,
    DailyReportResponse,
)
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/daily", response_model=DailyReportResponse)
async def get_daily_report(
    course_id: str = Query(...),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get a daily attendance report for a course."""
    return await report_service.get_daily_report(course_id, date)


@router.get("/weekly", response_model=list[DailyReportResponse])
async def get_weekly_report(
    course_id: str = Query(...),
    start_date: str = Query(
        ..., description="Start date in YYYY-MM-DD format"
    ),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """
    Get a weekly attendance report.

    Returns daily reports for 7 days starting from start_date.
    """
    from datetime import datetime, timedelta

    reports = []
    base_date = datetime.strptime(start_date, "%Y-%m-%d")

    for i in range(7):
        day = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        report = await report_service.get_daily_report(course_id, day)
        reports.append(report)

    return reports


@router.get("/monthly", response_model=list[DailyReportResponse])
async def get_monthly_report(
    course_id: str = Query(...),
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get a monthly attendance report (daily breakdown)."""
    from datetime import datetime, timedelta
    import calendar

    _, days_in_month = calendar.monthrange(year, month)
    reports = []

    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        report = await report_service.get_daily_report(course_id, date_str)
        # Only include days that have data
        if report.total_students > 0:
            reports.append(report)

    return reports


@router.get(
    "/course/{course_id}",
    response_model=list[StudentAttendanceSummary],
)
async def get_course_report(
    course_id: str,
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get a course-wide attendance summary for all enrolled students."""
    return await report_service.get_course_report(course_id)


@router.get("/student/{student_id}")
async def get_student_report(
    student_id: str,
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get a student's attendance summary across all enrolled courses."""
    return await report_service.get_student_report(student_id)


@router.get("/export")
async def export_report(
    format: str = Query("csv"),
    course_id: str | None = Query(None),
    student_id: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """
    Export attendance data as a CSV file.

    Filters can be combined: course, student, date range.
    """
    rows = await report_service.get_report_csv_data(
        course_id=course_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    if format == "pdf":

        buffer = io.BytesIO()

        pdf = SimpleDocTemplate(buffer,pagesize=landscape(A4))

        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                "Attendance Report",
                styles["Heading2"]
            )
        )

        elements.append(
            Spacer(1, 12)
        )


        if rows:

            data = [
                list(rows[0].keys())
            ]

            for row in rows:
                data.append(
                    list(row.values())
                )

        else:

            data = [
                ["No data found"]
            ]


        table = Table(data,repeatRows=1)

        table.setStyle(
            TableStyle([
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("FONTSIZE", (0,0), (-1,-1), 7),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (0,0), (-1,0), "CENTER"),
            ])
        )


        elements.append(table)

        pdf.build(elements)

        pdf_bytes = buffer.getvalue()

        buffer.close()


        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                "attachment; filename=attendance_report.pdf"
            },
        )

    # Build CSV in memory
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("No data found for the given filters.\n")

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=attendance_report.csv"
        },
    )
