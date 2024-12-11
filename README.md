# Movie Max API Documentation

## Overview
The Movie Max API provides endpoints for managing users, interacting with a watchlist, and retrieving data from the TMDB API. This document outlines the available routes and their functionalities.

---

Unit Tests and Smoketests links

Google doc with screenshots of unit tests and smoke test passing
https://docs.google.com/document/d/1ODJwDcbWrOs2NB70VWrl8NrUR4SNIbCaSKmT9Ij_Ay0/edit?usp=sharing

## Root Routes

### 1. Root Endpoint
- **URL:** `/`
- **Method:** `GET`
- **Description:** Returns a welcome message for the Movie Max application.
- **Response Example:**
  ```json
  {
      "message": "Welcome to Movie Max"
  }
  ```

### 2. API Root
- **URL:** `/api`
- **Method:** `GET`
- **Description:** Returns a welcome message for the Movie Max API.
- **Response Example:**
  ```json
  {
      "message": "Welcome to Movie Max API!"
  }
  ```

---

## Health Checks

### 3. Health Check
- **URL:** `/api/health`
- **Method:** `GET`
- **Description:** Checks the health status of the service.
- **Response Example:**
  ```json
  {
      "status": "healthy"
  }
  ```

### 4. Database Health Check
- **URL:** `/api/db-check`
- **Method:** `GET`
- **Description:** Verifies the database connection and checks if the `watchlist` table exists.
- **Response Example:**
  ```json
  {
      "database_status": "healthy"
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<error-message>"
  }
  ```

---

## User Management

### 5. Create User
- **URL:** `/api/create-user`
- **Method:** `POST`
- **Description:** Creates a new user.
- **Request Body Example:**
  ```json
  {
      "username": "example_user",
      "password": "secure_password"
  }
  ```
- **Response Example:**
  ```json
  {
      "status": "user added",
      "username": "example_user"
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<error-message>"
  }
  ```

### 6. Delete User
- **URL:** `/api/delete-user`
- **Method:** `DELETE`
- **Description:** Deletes an existing user.
- **Request Body Example:**
  ```json
  {
      "username": "example_user"
  }
  ```
- **Response Example:**
  ```json
  {
      "status": "user deleted",
      "username": "example_user"
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<error-message>"
  }
  ```

### 7. Login
- **URL:** `/api/login`
- **Method:** `POST`
- **Description:** Logs in a user.
- **Request Body Example:**
  ```json
  {
      "username": "example_user",
      "password": "secure_password"
  }
  ```
- **Response Example:**
  ```json
  {
      "message": "User example_user logged in successfully."
  }
  ```
- **Error Responses:**
  - Invalid credentials:
    ```json
    {
        "error": "Invalid username or password."
    }
    ```
  - Other errors:
    ```json
    {
        "error": "An unexpected error occurred."
    }
    ```

### 8. Logout
- **URL:** `/api/logout`
- **Method:** `POST`
- **Description:** Logs out a user.
- **Request Body Example:**
  ```json
  {
      "username": "example_user"
  }
  ```
- **Response Example:**
  ```json
  {
      "message": "User example_user logged out successfully."
  }
  ```
- **Error Responses:**
  - User not found:
    ```json
    {
        "error": "<error-message>"
    }
    ```
  - Other errors:
    ```json
    {
        "error": "An unexpected error occurred."
    }
    ```

---

## Movie API Integration

### 9. Search Movie
- **URL:** `/api/search/movie`
- **Method:** `GET`
- **Description:** Searches for a movie using the TMDB API.
- **Query Parameters:**
  - `query` (required): The movie title to search for.
- **Response Example:**
  ```json
  {
      "status": "success",
      "results": [
          {
              "title": "Inception",
              "movie_id": 12345,
              "release_date": "2010-07-16",
              "overview": "A thief who steals corporate secrets...",
              "vote_average": 8.8
          }
      ]
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<Error searching movie:>"
  }
  ```

### 10. Get Movie Details
- **URL:** `/api/movie/<int:movie_id>`
- **Method:** `GET`
- **Description:** Retrieves detailed information about a movie by its ID.
- **Response Example:**
  ```json
  {
      "status": "success",
      "movie": {
          "title": "Inception",
          "overview": "A thief who steals corporate secrets...",
          "release_date": "2010-07-16",
          "vote_average": 8.8
      }
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<Error fetching movie details:>"
  }
  ```

### 11. Get Movie Providers
- **URL:** `/api/movie/<int:movie_id>/watch/providers`
- **Method:** `GET`
- **Description:** Retrieves watch providers for a specific movie.
- **Response Example:**
  ```json
  {
      "status": "success",
      "providers": {
          "US": {
              "flatrate": [
                  {
                      "provider_name": "Netflix"
                  }
              ]
          }
      }
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<Error getting watch providers>"
  }
  ```

### 12. Get Recommendations
- **URL:** `/api/movie/<int:movie_id>/recommendations`
- **Method:** `GET`
- **Description:** Fetches movie recommendations based on a movie ID.
- **Response Example:**
  ```json
  {
      "status": "success",
      "recommendations": [
          {
              "title": "Interstellar",
              "overview": "A team of explorers travel through...",
              "release_date": "2014-11-07",
              "vote_average": 8.6
          }
      ]
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<Error fetching recommendations>"
  }
  ```

### 13. Get Popular Movies
- **URL:** `/api/movie/popularity`
- **Method:** `GET`
- **Description:** Retrieves the most popular movies.
- **Query Parameters:**
  - `page` (optional): The page of results to retrieve (default is 1).
- **Response Example:**
  ```json
  {
      "status": "success",
      "popular_movies": [
          {
              "title": "Avatar",
              "overview": "A paraplegic Marine dispatched to the moon Pandora...",
              "release_date": "2009-12-18",
              "vote_average": 7.8
          }
      ]
  }
  ```
- **Error Response:**
  ```json
  {
      "error": "<Error fetching popular movies:>"
  }
  ```

---

