﻿# ChefInProgress: Online Recipe Finder  
This project was developed as part of the Web Programming (006237-002) course at Sejong University during student exchange from Universiti Malaya. **ChefInProgress** is a dynamic recipe-sharing platform that allows users to upload, manage, and explore a wide range of cooking recipes. It also integrates AI to generate recipe ideas based on user-input ingredients.

---

## 🚀 Features

- **Recipe CRUD**: Users can Create, Read, Update, and Delete their own recipes.
- **Search & Filter**: Search recipes by title and filter by cuisine/category.
- **Saved Recipes**: Users can bookmark their favorite recipes with pagination support.
- **Profile Management**: Update profile info, password, and profile picture.
- **AI-Powered Recipes**: Google Gemini AI integration to generate creative recipes based on ingredients.
- **Interactive UI**: Built with responsive and aesthetic design using Material Design Bootstrap (MDBootstrap).

---

## 🛠️ Tech Stack

| Component         | Technology                          |
|------------------|-------------------------------------|
| Frontend         | HTML, CSS, JavaScript, MDBootstrap  |
| Backend          | Python Flask                        |
| Database         | MongoDB (Compass)                   |
| AI Integration   | Google Gemini API                   |
| Templating       | Jinja2                              |

---

## 🧠 Core Functionalities

- **Authentication**: User login, registration, and secure sessions.
- **AI Recipe Generator**: Real-time AI responses with stored history.
- **Profile Dashboard**: View and manage saved/created recipes.
- **Data Persistence**: Uses NoSQL MongoDB for user & recipe data.
- **Flash Messaging**: User feedback for each action (e.g., success, error).

---

## 📊 Database Collections

- **Recipe**: Title, ingredients, steps, images, category, prepared_by.
- **User**: Username, email, hashed password, profile picture, saved recipes.
- **Googleai_text**: AI prompt, response, user email, and timestamp.

---

## 📈 Future Improvements

- Recipe Rating & Feedback System
- Comments and Social Interactions
- Mobile App Version
- Online Subscription for AI Meal Plans
- Advanced Image Handling (drag-and-drop, real-time preview)
