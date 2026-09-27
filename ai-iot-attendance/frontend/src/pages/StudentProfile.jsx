import { useEffect, useState } from "react";
import {
    getStudentMe,
    changeStudentPassword,
} from "../api/students";
import "./StudentProfile.css";
import Loader from "../components/Loader";



function StudentProfile() {

    const [student, setStudent] = useState(null);

    const [loading, setLoading] = useState(true);

    const [message, setMessage] = useState("");


    const [passwordForm, setPasswordForm] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });


    const [passwordMessage, setPasswordMessage] = useState("");

    const [changingPassword, setChangingPassword] = useState(false);



    const loadProfile = async () => {

        try {

            const data = await getStudentMe();

            setStudent(data);

        } catch (error) {

            setMessage(
                error.message || "Failed to load profile."
            );

        } finally {

            setLoading(false);

        }

    };



    useEffect(() => {

        loadProfile();

    }, []);




    const handlePasswordChange = (e) => {

        setPasswordForm({
            ...passwordForm,
            [e.target.name]: e.target.value,
        });

    };




    const handleChangePassword = async (e) => {

        e.preventDefault();


        if (
            !passwordForm.current_password ||
            !passwordForm.new_password
        ) {

            setPasswordMessage(
                "Please fill all password fields."
            );

            return;

        }


        if (
            passwordForm.new_password !==
            passwordForm.confirm_password
        ) {

            setPasswordMessage(
                "New passwords do not match."
            );

            return;

        }



        setChangingPassword(true);
        setPasswordMessage("");



        try {


            await changeStudentPassword({

                current_password:
                    passwordForm.current_password,

                new_password:
                    passwordForm.new_password,

            });



            setPasswordMessage(
                "Password changed successfully."
            );


            setPasswordForm({

                current_password: "",
                new_password: "",
                confirm_password: "",

            });



        } catch (error) {


            setPasswordMessage(
                error.message || "Failed to change password."
            );


        } finally {

            setChangingPassword(false);

        }

    };





    if (loading) {

        return (

            <Loader/>

        );

    }





    return (

        <div className="student-profile-page">


            <h1>
                My Profile
            </h1>




            {message && (

                <p className="student-profile-message">
                    {message}
                </p>

            )}






            {student && (
                <div className="student-card">
                    
                    <div className="student-profile-card">

                        <h2>
                            Profile Information
                        </h2>



                        <p>
                            <strong>Name:</strong>{" "}
                            {student.name}
                        </p>


                        <p>
                            <strong>Student ID:</strong>{" "}
                            {student.student_id}
                        </p>


                        <p>
                            <strong>Email:</strong>{" "}
                            {student.email}
                        </p>


                        <p>
                            <strong>Department:</strong>{" "}
                            {student.department}
                        </p>


                        <p>
                            <strong>Batch:</strong>{" "}
                            {student.batch}
                        </p>


                    </div>

                    <div className="student-password-card">

                        <h2>
                            Change Password
                        </h2>



                        <form onSubmit={handleChangePassword}>


                            <div className="student-password-form-group">

                                <label>
                                    Current Password
                                </label>

                                <input
                                    type="password"
                                    name="current_password"
                                    value={
                                        passwordForm.current_password
                                    }
                                    onChange={handlePasswordChange}
                                />

                            </div>




                            <div className="student-password-form-group">

                                <label>
                                    New Password
                                </label>


                                <input
                                    type="password"
                                    name="new_password"
                                    value={
                                        passwordForm.new_password
                                    }
                                    onChange={handlePasswordChange}
                                />

                            </div>





                            <div className="student-password-form-group">

                                <label>
                                    Confirm New Password
                                </label>


                                <input
                                    type="password"
                                    name="confirm_password"
                                    value={
                                        passwordForm.confirm_password
                                    }
                                    onChange={handlePasswordChange}
                                />

                            </div>





                            {passwordMessage && (

                                <p className="student-password-message">
                                    {passwordMessage}
                                </p>

                            )}






                            <button
                                type="submit"
                                className="student-password-button"
                                disabled={changingPassword}
                            >

                                {
                                    changingPassword
                                        ? "Changing..."
                                        : "Change Password"
                                }

                            </button>


                        </form>


                    </div>

                </div>


            )}





        </div>

    );

}


export default StudentProfile;