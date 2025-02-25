import React, {useState} from "react";
import { Calendar } from "react-calendar";
import "react-calendar/dist/Calendar.css";

export default function CalendarVeiw() {
    const [value, onChange]= useState(new Date());
    return(
        <div className="container mx-auto p-4 ">
            <h1>
                Calendar
            </h1>
            <Calendar
                className={""}
                />
        </div>
    )
}