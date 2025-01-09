# 🏋️‍♂️ Fitness Tracker System 🏃‍♀️

## 📖 Overview
The **Fitness Tracker System** is a web application designed to analyze exercise performance from video inputs, log user progress, and provide insights into workouts. The system supports multiple exercises, including **Pull-Ups**, **Push-Ups**, **Squats**, and more, with features to track repetitions, sets, duration, difficulty level, calories burned, and user-provided notes.

---

## ✨ Features
- 🎥 **Video-Based Analysis**: Analyze user workout videos to extract detailed exercise metrics.
- 📝 **User Notes**: Attach notes to workouts for personalized feedback and tracking.
- 📊 **Exercise Logs**: Store and view logs for exercises with key metrics.
- 🔒 **User Authentication**: Secure login and registration system.
- 📅 **Progress Tracking**: View historical performance data.
- 💡 **Dynamic Insights**: Difficulty levels, calories burned, and personalized recommendations.

---

## 📂 Project Structure
```yaml
📦 Fitness Tracker System
├── 📂 app
│   ├── 📂 static
│   │   ├── 📂 css
│   │       
│   ├── 📂 templates
│   │   ├── dashboard.html
│   │   └── pullups_video.html
│   │   └── pushups_video.html
│   │   └── signup.html
│   │   └── squats_video.html
        . . .
        . . .
│   ├── app.py
├── 📂 captured_videos
├── 📂 instance
│   │   └── fitness_tracker.db
├── README.md
```

## 🛠️ Technologies Used
- Backend: Flask 🐍
- Frontend: HTML5, CSS3 🎨
- Database: SQLite / PostgreSQL 🗃️
- Video Analysis: OpenCV + Mediapipe 🎥
- Authentication: Flask-Login 🔒

## 📜 Routes

| **Method** | **Route**                  | **Description**                    |
|------------|----------------------------|------------------------------------|
| `POST`     | `/capture_video/<exercise>`| Upload and analyze workout video. |
| `GET`      | `/dashboard`               | View user exercise logs.          |
| `GET`      | `/login`                   | User login page.                  |
| `POST`     | `/logout`                  | Logout user.                      |


## 📜 License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute this project as long as the original license is included.  
See the [LICENSE](./LICENSE) file for details.

---


*Contributions are always welcome! Feel free to fork this repository and create a pull request.*

---

## 🌟 Acknowledgements

A huge thanks to the following resources and libraries that made this project possible:

- **[OpenCV](https://opencv.org/):** For its powerful computer vision capabilities.  
- **[Mediapipe](https://mediapipe.dev/):** For efficient pose estimation and tracking.  
- **[Flask Documentation](https://flask.palletsprojects.com/):** For excellent guidance and examples.  
- **The Open-Source Community:** For inspiring innovative ideas and solutions.

---

Thank you for checking out the project! 🚀 If you find it useful, don't forget to ⭐ the repository!

