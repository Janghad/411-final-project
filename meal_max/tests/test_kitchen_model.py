from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    # Call the function
    create_meal(meal="Lasagna", cuisine="Italian", price=12.99, difficulty="LOW")

    # Set the SQL query we expect to be executed
    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)
    # Check that the cursor executed the query with the correct arguments
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Check that the arguments match the expected values
    expected_arguments = ("Lasagna", "Italian", 12.99, "LOW")
    assert actual_arguments == ("Lasagna", "Italian", 12.99, "LOW"), f"The SQL arguments did not match, expected: {expected_arguments}, actual: {actual_arguments}"

def test_create_meal_duplicate(mock_cursor):
    """test create_meal with duplicate arguments (should raise an error)"""
    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Call the function and expect it to raise a ValueError
    with pytest.raises(ValueError, match="Meal with name 'Lasagna' already exists"):
        create_meal(meal="Lasagna", cuisine="Italian", price=12.99, difficulty="LOW")

def test_create_meal_invalid_price(mock_cursor):
    """test create_meal with an invalid price (should raise an error)"""

    # Call the function with an invalid price (0)
    with pytest.raises(ValueError, match="Invalid price: 0. Price must be a positive number."):
        create_meal(meal="Lasagna", cuisine="Italian", price=0, difficulty="LOW")
    
    # Call the function with an invalid price (-5)
    with pytest.raises(ValueError, match="Invalid price: -5. Price must be a positive number."):
        create_meal(meal="Lasagna", cuisine="Italian", price=-5, difficulty="LOW")

    # Call the function with an invalid price (string)
    with pytest.raises(ValueError, match="Invalid price: invalid. Price must be a positive number."):
        create_meal(meal="Lasagna", cuisine="Italian", price="invalid", difficulty="LOW")

def test_create_meal_invalid_difficulty(mock_cursor):
    """test create_meal with an invalid difficulty (should raise an error)"""

    # Call the function with an invalid difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: MEDIUM. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Lasagna", cuisine="Italian", price=12.99, difficulty="MEDIUM")
    
    # Call the function with an invalid difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: low. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Lasagna", cuisine="Italian", price=12.99, difficulty="low")

def test_clear_meals(mock_cursor, mocker):
    """Test clearing all meals."""

    mocker.patch.dict(
        "os.environ", {"SQL_CREATE_TABLE_PATH": "sql/create_meal_table.sql"}
    )
    mock_open = mocker.patch(
        "builtins.open", mocker.mock_open(read_data="CREATE TABLE meals ...")
    )

    clear_meals()

    mock_open.assert_called_once_with("sql/create_meal_table.sql", "r")
    mock_cursor.executescript.assert_called_once()


def test_delete_meal(mock_cursor):

    # Set the return value for the fetchone method
    mock_cursor.fetchone.return_value = ([False])

    # Call the function
    delete_meal(meal_id=1)

    # Normalize the SQL query for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to 'execute()' using 'call_args_list'
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

######################################################
#
#    Get Song
#
######################################################

# def test_get_leaderboard(mock_cursor):
    
def test_get_meal_by_id(mock_cursor):
     # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Lasagna", "Italian", 12.99, "MED", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Lasagna", "Italian", 12.99, "MED")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_bad_id(mock_cursor):
    """Test error when trying to get a non-existent meal by ID."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to get a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted(mock_cursor):
    """Test error when trying to get a meal that's already marked as deleted by ID."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = (1, "Lasagna", "Italian", 12.99, "MED", True)

    # Expect a ValueError when attempting to get a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists (name = "Lasagna")
    mock_cursor.fetchone.return_value = (1, "Lasagna", "Italian", 12.99, "MED", False)

    # Call the function and check the result
    result = get_meal_by_name("Lasagna")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Lasagna", "Italian", 12.99, "MED")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Lasagna",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_bad_name(mock_cursor):
    """Test error when trying to get a non-existent meal by name."""

    # Simulate that no meal exists with the given name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to get a non-existent meal
    with pytest.raises(ValueError, match="Meal with name Lasagna not found"):
        get_meal_by_name("Lasagna")

def test_get_meal_by_name_deleted(mock_cursor):
    """Test error when trying to get a meal that's already marked as deleted by name."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = (1, "Lasagna", "Italian", 12.99, "MED", True)

    # Expect a ValueError when attempting to get a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with name Lasagna has been deleted"):
        get_meal_by_name("Lasagna")

def test_update_meal_stats(mock_cursor):
    # Simulate that the meal exists
    mock_cursor.fetchone.return_value = ([False])

    # Call the function
    update_meal_stats(meal_id=1, result="win")

    # Set the SQL query we expect to be executed
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")

    # Check that the cursor executed the query with the correct arguments
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Check that the arguments match the expected values
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL arguments did not match, expected: {expected_arguments}, actual: {actual_arguments}"

def test_update_meal_stats_loss(mock_cursor):
    # Simulate that the meal exists
    mock_cursor.fetchone.return_value = ([False])

    # Call the function
    update_meal_stats(meal_id=1, result="loss")

    # Set the SQL query we expect to be executed
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1 WHERE id = ?")

    # Check that the cursor executed the query with the correct arguments
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Check that the arguments match the expected values
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL arguments did not match, expected: {expected_arguments}, actual: {actual_arguments}"

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error when trying to update meal stats with an invalid result."""

    # Simulate that the meal exists
    mock_cursor.fetchone.return_value = ([False])

    # Expect a ValueError when attempting to update stats with an invalid result
    with pytest.raises(ValueError, match="Invalid result: INVALID. Expected 'win' or 'loss'."):
        update_meal_stats(meal_id=1, result="INVALID")

def test_update_meal_stats_not_found(mock_cursor):
    """Test error when trying to update stats for a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to update stats for a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")
    
def test_update_meal_stats_deleted(mock_cursor):
    """Test error when trying to update stats for a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to update stats for a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        update_meal_stats(999, "win")

######################################################
#
#    Get Leaderboard
#
######################################################

def test_get_leaderboard_wins(mock_cursor):
    # Simulate the leaderboard data
    mock_cursor.fetchall.return_value = [
        (1, "Burger", "American", 9.99, "LOW", 10, 7, 0.7, False),
        (2, "Sushi", "Japanese", 15.99, "HIGH", 8, 6, 0.75, False),
        (3, "Lasagna", "Italian", 12.99, "MED", 5, 3, 0.6, False)
    ]

    # Call the function
    leaderboard = get_leaderboard(sort_by="wins")

    # Expected leaderboard based on the simulated fetchall return value
    expected_leaderboard = [
        {"id": 1, "meal": "Burger", "cuisine": "American", "price": 9.99, "difficulty": "LOW", "battles": 10, "wins": 7, "win_pct": 70.0},
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.99, "difficulty": "HIGH", "battles": 8, "wins": 6, "win_pct": 75.0},
        {"id": 3, "meal": "Lasagna", "cuisine": "Italian", "price": 12.99, "difficulty": "MED", "battles": 5, "wins": 3, "win_pct": 60.0}
    ]

    # Ensure the leaderboard matches the expected output
    assert leaderboard == expected_leaderboard, f"Expected {expected_leaderboard}, got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_win_pct(mock_cursor):
    # Simulate the leaderboard data
    mock_cursor.fetchall.return_value = [
        (2, "Sushi", "Japanese", 15.99, "HIGH", 8, 6, 0.75),
        (1, "Burger", "American", 9.99, "LOW", 10, 7, 0.7),
        (3, "Lasagna", "Italian", 12.99, "MED", 5, 3, 0.6),
    ]

    # Call the function
    leaderboard = get_leaderboard(sort_by="win_pct")

    # Expected leaderboard based on the simulated fetchall return value
    expected_leaderboard = [
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.99, "difficulty": "HIGH", "battles": 8, "wins": 6, "win_pct": 75.0},
        {"id": 1, "meal": "Burger", "cuisine": "American", "price": 9.99, "difficulty": "LOW", "battles": 10, "wins": 7, "win_pct": 70.0},
        {"id": 3, "meal": "Lasagna", "cuisine": "Italian", "price": 12.99, "difficulty": "MED", "battles": 5, "wins": 3, "win_pct": 60.0}
    ]

    # Ensure the leaderboard matches the expected output
    assert leaderboard == expected_leaderboard, f"Expected {expected_leaderboard}, got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct FROM meals WHERE deleted = false AND battles > 0 ORDER BY win_pct DESC")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_default(mock_cursor):
    # Simulate the leaderboard data
    mock_cursor.fetchall.return_value = [
        (1, "Burger", "American", 9.99, "LOW", 10, 7, 0.7),
        (2, "Sushi", "Japanese", 15.99, "HIGH", 8, 6, 0.75),
        (3, "Lasagna", "Italian", 12.99, "MED", 5, 3, 0.6),
    ]

    # Call the function without specifying a sort_by parameter
    leaderboard = get_leaderboard()

    # Expected leaderboard based on the simulated fetchall return value
    expected_leaderboard = [
        {"id": 1, "meal": "Burger", "cuisine": "American", "price": 9.99, "difficulty": "LOW", "battles": 10, "wins": 7, "win_pct": 70.0},
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.99, "difficulty": "HIGH", "battles": 8, "wins": 6, "win_pct": 75.0},
        {"id": 3, "meal": "Lasagna", "cuisine": "Italian", "price": 12.99, "difficulty": "MED", "battles": 5, "wins": 3, "win_pct": 60.0}
    ]

    # Ensure the leaderboard matches the expected output
    assert leaderboard == expected_leaderboard, f"Expected {expected_leaderboard}, got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_parameter(mock_cursor):
    # Call the function with an invalid sort_by parameter
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        get_leaderboard(sort_by="invalid")

    # Ensure no SQL query was executed when an invalid parameter is provided
    assert mock_cursor.execute.call_count == 0, "No SQL query should be executed for an invalid sort_by parameter."