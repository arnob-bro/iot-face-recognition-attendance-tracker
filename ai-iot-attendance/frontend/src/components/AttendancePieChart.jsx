import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

import "./AttendancePieChart.css";


function AttendancePieChart({ reports }) {


    const totals = reports.reduce(
        (acc, report) => {

            acc.present += report.present || 0;
            acc.absent += report.absent || 0;
            acc.late += report.late || 0;

            return acc;

        },
        {
            present: 0,
            absent: 0,
            late: 0,
        }
    );


    const data = [
        {
            name: "Present",
            value: totals.present,
        },
        {
            name: "Late",
            value: totals.late,
        },
        {
            name: "Absent",
            value: totals.absent,
        },
    ];


    const COLORS = [
        "#22c55e",
        "#f59e0b",
        "#ef4444",
    ];


    return (

        <div className="attendance-pie-card">

            <h2>
                Attendance Distribution
            </h2>


            <ResponsiveContainer
                width="100%"
                height={320}
            >

                <PieChart>


                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        dataKey="value"
                        label
                    >

                        {
                            data.map(
                                (entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={COLORS[index]}
                                    />
                                )
                            )
                        }


                    </Pie>


                    <Tooltip />


                    <Legend />


                </PieChart>


            </ResponsiveContainer>


        </div>

    );

}


export default AttendancePieChart;