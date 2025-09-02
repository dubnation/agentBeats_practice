from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import re

def press_cell(num: int, driver=None, url="https://ttt.puppy9.com/"):
    """
    Presses a cell on the tic-tac-toe game board.
    
    Args:
        num: Integer between 0-8 representing the cell position
             0 1 2
             3 4 5  
             6 7 8
        driver: Selenium WebDriver instance (optional, will create one if not provided)
        url: URL of the tic-tac-toe game
    
    Returns:
        bool: True if cell was successfully pressed, False otherwise
    """
    
    # Validate input
    if not isinstance(num, int) or num < 0 or num > 8:
        raise ValueError("num must be an integer between 0 and 8")
    
    # Create driver if not provided
    created_driver = False
    if driver is None:
        driver = webdriver.Chrome()
        created_driver = True
    
    try:
        # Navigate to the game if needed
        if driver.current_url != url:
            driver.get(url)
        
        # Wait for game board to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "gameBoard"))
        )
        
        # Find the cell with the specified data-index
        cell_selector = f'button[data-index="{num}"]'
        
        try:
            # Wait for the cell to be clickable
            cell = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, cell_selector))
            )
            
            # Click the cell
            cell.click()
            return True
            
        except TimeoutException:
            print(f"Cell {num} is not clickable (may already be occupied)")
            return False
            
        except ElementClickInterceptedException:
            print(f"Cell {num} click was intercepted (may be disabled)")
            return False
            
        except NoSuchElementException:
            print(f"Cell {num} not found")
            return False
    
    except Exception as e:
        print(f"Error pressing cell {num}: {e}")
        return False
    
    finally:
        # Close driver if we created it
        if created_driver:
            driver.quit()



def getCurrGameStatus(driver=None, url="https://ttt.puppy9.com/"):
    """
    Extracts the current tic-tac-toe game state from the webpage.
    
    Args:
        driver: Selenium WebDriver instance (optional, will create one if not provided)
        url: URL of the tic-tac-toe game
    
    Returns:
        dict: {'currentGameBoard': 2D array, 'gameStatus': 'win'|'lose'|'still playing'}
    """
    
    # Create driver if not provided
    created_driver = False
    if driver is None:
        driver = webdriver.Chrome()  # You may need to specify path to chromedriver
        created_driver = True
    
    try:
        # Navigate to the game if needed
        if driver.current_url != url:
            driver.get(url)
        
        # Wait for game board to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "gameBoard"))
        )
        
        # Initialize 3x3 game board
        game_board = [['', '', ''], ['', '', ''], ['', '', '']]
        
        # Extract board state from cells
        for i in range(9):
            try:
                # Find cell by data-index attribute
                cell = driver.find_element(By.CSS_SELECTOR, f'button[data-index="{i}"]')
                cell_text = cell.text.strip().lower()
                
                # Convert 1D index to 2D coordinates
                row = i // 3
                col = i % 3
                
                # Set cell value ('x', 'o', or empty string)
                if cell_text in ['x', 'o']:
                    game_board[row][col] = cell_text
                else:
                    game_board[row][col] = ''
                    
            except NoSuchElementException:
                # Cell might not exist or be accessible
                row = i // 3
                col = i % 3
                game_board[row][col] = ''
        
        # Determine game status
        game_status = determine_game_status(driver, game_board)
        
        return {
            'currentGameBoard': game_board,
            'gameStatus': game_status
        }
    
    finally:
        # Close driver if we created it
        if created_driver:
            driver.quit()

def determine_game_status(driver, board):
    """
    Determines the current game status based on DOM elements and board state.
    
    Args:
        driver: Selenium WebDriver instance
        board: 2D array representing current board state
    
    Returns:
        str: 'win', 'lose', or 'still playing'
    """
    
    # Check for win message in congratulations div
    try:
        congratulations = driver.find_element(By.ID, "congratulations")
        if congratulations.is_displayed():
            congrats_text = congratulations.text.lower()
            if "you won" in congrats_text or "you win" in congrats_text:
                return 'win'
    except NoSuchElementException:
        pass
    
    # Check game status div
    try:
        game_status_elem = driver.find_element(By.ID, "gameStatus")
        status_text = game_status_elem.text.lower()
        
        if "you won" in status_text or "you win" in status_text:
            return 'win'
        elif "you lost" in status_text or "you lose" in status_text or "computer wins" in status_text:
            return 'lose'
    except NoSuchElementException:
        pass
    
    # Check for win/lose conditions based on board state
    # Check for winning combinations first (games can end before board is full)
    if has_winning_combination(board, 'x'):  # Player (X) wins
        return 'win'
    elif has_winning_combination(board, 'o'):  # Computer (O) wins
        return 'lose'
    
    # If no winning combination, check if board is full (tie) or game is still ongoing
    if is_board_full(board):
        # This would be a tie, but since we only have 3 options,
        # we'll call it 'still playing' or you might want to add 'tie'
        return 'still playing'
    
    return 'still playing'


def getWinningNumber(driver=None, url="https://ttt.puppy9.com/"):
    """
    Extracts the winning number from the tic-tac-toe game when you win.
    
    Args:
        driver: Selenium WebDriver instance (optional, will create one if not provided)
        url: URL of the tic-tac-toe game
    
    Returns:
        str: The winning number (e.g., "20250902093507") or None if not found
    """
    
    # Create driver if not provided
    created_driver = False
    if driver is None:
        driver = webdriver.Chrome()
        created_driver = True
    
    try:
        # Navigate to the game if needed
        if driver.current_url != url:
            driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Try to find the congratulations element with the winning number
        try:
            # Look for the congratulations div
            congratulations = driver.find_element(By.ID, "congratulations")
            if congratulations.is_displayed():
                congrats_text = congratulations.text
                
                # Extract number from text like "You win! Here's your secret: 20250902093507"
                number_match = re.search(r'secret:\s*(\d+)', congrats_text)
                if number_match:
                    return number_match.group(1)
        except NoSuchElementException:
            pass
        
        # Alternative: look for any element containing the winning pattern
        try:
            # Search for any element containing the secret number pattern
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'secret:')]")
            for element in elements:
                if element.is_displayed():
                    text = element.text
                    number_match = re.search(r'secret:\s*(\d+)', text)
                    if number_match:
                        return number_match.group(1)
        except NoSuchElementException:
            pass
        
        # Another approach: look for long numbers in the page
        try:
            # Find elements with long numeric strings (13+ digits)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            long_numbers = re.findall(r'\b\d{13,}\b', page_text)
            if long_numbers:
                # Return the first long number found (likely the winning number)
                return long_numbers[0]
        except NoSuchElementException:
            pass
        
        return None
    
    finally:
        # Close driver if we created it
        if created_driver:
            driver.quit()

def is_board_full(board):
    """
    Check if the board is completely filled.
    
    Args:
        board: 2D array representing the game board
    
    Returns:
        bool: True if board is full
    """
    for row in board:
        for cell in row:
            if cell == '':
                return False
    return True


def has_winning_combination(board, player):
    """
    Check if a player has a winning combination on the board.
    
    Args:
        board: 2D array representing the game board
        player: 'x' or 'o'
    
    Returns:
        bool: True if player has winning combination
    """
    player = player.lower()
    
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    
    return False