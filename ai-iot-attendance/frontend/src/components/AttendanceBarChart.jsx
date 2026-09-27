import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Label,
} from "recharts";

import "./AttendanceCharts.css";


function AttendanceBarChart({ reports }) {


    if (!reports || reports.length === 0) {

        return (
            <div className="chart-card">
                <h3>Attendance Bar Chart</h3>
                <p>No data available.</p>
            </div>
        );

    }


    const chartData = reports.map((report) => {

        let label = report.course_name;


        if (reports.length > 0) {

            const uniqueDates = [
                ...new Set(
                    reports.map((item) => item.date)
                )
            ];


            // Weekly and monthly reports
            // show dates on X-axis
            if (uniqueDates.length > 1) {
                label = report.date;
            }
        }


        return {
            name: label,

            course: report.course_name,

            date: report.date,

            Present: report.present || 0,

            Absent: report.absent || 0,

            Late: report.late || 0,
        };

    });

    const CustomTooltip = ({ active, payload }) => {

        if (active && payload && payload.length) {

            const item = payload[0].payload;


            return (
                <div className="chart-tooltip">

                    <p>
                        Course: {item.course}
                    </p>

                    <p>
                        Date: {item.date}
                    </p>


                    <p className="chart-present">
                        Present: {item.Present}
                    </p>


                    <p className="chart-late">
                        Late: {item.Late}
                    </p>


                    <p className="chart-absent">
                        Absent: {item.Absent}
                    </p>

                </div>
            );
        }


        return null;
    };



    return (

        <div className="chart-card">

            <h3>
                Attendance Overview
            </h3>


            <ResponsiveContainer
                width="100%"
                height={400}
            >

                <BarChart
                    data={chartData}
                    className="attendance-bar-chart"
                >

                    <CartesianGrid
                        strokeDasharray="3 3"
                    />

                    <XAxis
                        dataKey="name"
                        tick={{ fontSize: 12 }}
                        angle={-35}
                        textAnchor="end"
                        height={60}
                    >
                        <Label
                            value="Course / Date"
                            position="insideBottom"
                            offset={-45}
                        />
                    </XAxis>

                    <YAxis
                        allowDecimals={false}
                        domain={[0, "auto"]}
                        tick={{ fontSize: 12 }}
                    >
                        <Label
                            value="Number of Students"
                            angle={-90}
                            position="insideLeft"
                        />
                    </YAxis>

                    <Tooltip
                        content={<CustomTooltip />}
                        wrapperClassName="attendance-chart-tooltip"
                    />

                    <Legend />


                    <Bar
                        dataKey="Present"
                        fill="#22c55e"
                        radius={[6, 6, 0, 0]}
                    />

                    <Bar
                        dataKey="Absent"
                        fill="#ef4444"
                        radius={[6, 6, 0, 0]}
                    />

                    <Bar
                        dataKey="Late"
                        fill="#f59e0b"
                        radius={[6, 6, 0, 0]}
                    />

                </BarChart>

            </ResponsiveContainer>


        </div>

    );

}


export default AttendanceBarChart;