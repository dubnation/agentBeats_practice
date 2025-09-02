#!/usr/bin/env python3
"""
Test suite for tictactoe_tool.py

This test suite covers:
- Helper functions (has_winning_combination, is_board_full, determine_game_status)
- Main function getCurrGameStatus with mocked Selenium components
- Various game scenarios and edge cases
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Import the functions to test
from tictactoe_tool import (
    getCurrGameStatus,
    has_winning_combination, 
    is_board_full,
    determine_game_status
)

class TestTicTacToeHelperFunctions(unittest.TestCase):
    """Test helper functions that don't require Selenium"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Empty board
        self.empty_board = [['', '', ''], ['', '', ''], ['', '', '']]
        
        # X wins horizontally (top row)
        self.x_wins_horizontal = [['x', 'x', 'x'], ['o', 'o', ''], ['', '', '']]
        
        # O wins vertically (left column)
        self.o_wins_vertical = [['o', 'x', ''], ['o', 'x', ''], ['o', '', 'x']]
        
        # X wins diagonally (main diagonal)
        self.x_wins_diagonal_main = [['x', 'o', ''], ['o', 'x', ''], ['', '', 'x']]
        
        # O wins diagonally (anti-diagonal)
        self.o_wins_diagonal_anti = [['', 'o', 'o'], ['x', 'o', ''], ['o', 'x', 'x']]
        
        # Full board, no winner (tie)
        self.full_board_tie = [['x', 'o', 'x'], ['o', 'o', 'x'], ['o', 'x', 'o']]
        
        # Partial board, game ongoing
        self.partial_board = [['x', 'o', ''], ['', 'x', ''], ['o', '', '']]

    def test_has_winning_combination_x_horizontal(self):
        """Test X winning horizontally"""
        self.assertTrue(has_winning_combination(self.x_wins_horizontal, 'x'))
        self.assertFalse(has_winning_combination(self.x_wins_horizontal, 'o'))
    
    def test_has_winning_combination_o_vertical(self):
        """Test O winning vertically"""
        self.assertTrue(has_winning_combination(self.o_wins_vertical, 'o'))
        self.assertFalse(has_winning_combination(self.o_wins_vertical, 'x'))
    
    def test_has_winning_combination_x_diagonal_main(self):
        """Test X winning on main diagonal"""
        self.assertTrue(has_winning_combination(self.x_wins_diagonal_main, 'x'))
        self.assertFalse(has_winning_combination(self.x_wins_diagonal_main, 'o'))
    
    def test_has_winning_combination_o_diagonal_anti(self):
        """Test O winning on anti-diagonal"""
        self.assertTrue(has_winning_combination(self.o_wins_diagonal_anti, 'o'))
        self.assertFalse(has_winning_combination(self.o_wins_diagonal_anti, 'x'))
    
    def test_has_winning_combination_no_winner(self):
        """Test no winning combination"""
        self.assertFalse(has_winning_combination(self.partial_board, 'x'))
        self.assertFalse(has_winning_combination(self.partial_board, 'o'))
        self.assertFalse(has_winning_combination(self.empty_board, 'x'))
        self.assertFalse(has_winning_combination(self.empty_board, 'o'))
    
    def test_has_winning_combination_case_insensitive(self):
        """Test case insensitivity"""
        self.assertTrue(has_winning_combination(self.x_wins_horizontal, 'X'))
        self.assertTrue(has_winning_combination(self.o_wins_vertical, 'O'))
    
    def test_is_board_full_empty(self):
        """Test empty board is not full"""
        self.assertFalse(is_board_full(self.empty_board))
    
    def test_is_board_full_partial(self):
        """Test partially filled board is not full"""
        self.assertFalse(is_board_full(self.partial_board))
    
    def test_is_board_full_complete(self):
        """Test completely filled board is full"""
        self.assertTrue(is_board_full(self.full_board_tie))
    
    def test_is_board_full_winner_but_not_full(self):
        """Test board with winner but not all cells filled"""
        self.assertFalse(is_board_full(self.x_wins_horizontal))
        self.assertFalse(is_board_full(self.o_wins_vertical))


class TestDetermineGameStatus(unittest.TestCase):
    """Test the determine_game_status function with mocked driver"""
    
    def setUp(self):
        """Set up mock driver for testing"""
        self.mock_driver = Mock()
        
        # Test boards
        self.x_wins_board = [['x', 'x', 'x'], ['o', 'o', ''], ['', '', '']]
        self.o_wins_board = [['o', 'x', ''], ['o', 'x', ''], ['o', '', 'x']]
        self.tie_board = [['x', 'o', 'x'], ['o', 'o', 'x'], ['o', 'x', 'o']]
        self.ongoing_board = [['x', 'o', ''], ['', 'x', ''], ['o', '', '']]
    
    def test_determine_game_status_win_from_congratulations(self):
        """Test win status detected from congratulations div"""
        # Mock congratulations element showing win
        mock_congrats = Mock()
        mock_congrats.is_displayed.return_value = True
        mock_congrats.text = "Congratulations! You won!"
        
        self.mock_driver.find_element.return_value = mock_congrats
        
        result = determine_game_status(self.mock_driver, self.ongoing_board)
        self.assertEqual(result, 'win')
    
    def test_determine_game_status_win_from_game_status(self):
        """Test win status detected from gameStatus div"""
        # Mock congratulations not found, but gameStatus shows win
        def side_effect(*args):
            if args[1] == "congratulations":
                from selenium.common.exceptions import NoSuchElementException
                raise NoSuchElementException()
            elif args[1] == "gameStatus":
                mock_status = Mock()
                mock_status.text = "You win this round!"
                return mock_status
        
        self.mock_driver.find_element.side_effect = side_effect
        
        result = determine_game_status(self.mock_driver, self.ongoing_board)
        self.assertEqual(result, 'win')
    
    def test_determine_game_status_lose_from_game_status(self):
        """Test lose status detected from gameStatus div"""
        def side_effect(*args):
            if args[1] == "congratulations":
                from selenium.common.exceptions import NoSuchElementException
                raise NoSuchElementException()
            elif args[1] == "gameStatus":
                mock_status = Mock()
                mock_status.text = "Computer wins! You lost."
                return mock_status
        
        self.mock_driver.find_element.side_effect = side_effect
        
        result = determine_game_status(self.mock_driver, self.ongoing_board)
        self.assertEqual(result, 'lose')
    
    def test_determine_game_status_win_from_board_state(self):
        """Test win status determined from board analysis when no DOM messages"""
        # Mock no congratulations or gameStatus elements
        from selenium.common.exceptions import NoSuchElementException
        self.mock_driver.find_element.side_effect = NoSuchElementException()
        
        result = determine_game_status(self.mock_driver, self.x_wins_board)
        self.assertEqual(result, 'win')
    
    def test_determine_game_status_lose_from_board_state(self):
        """Test lose status determined from board analysis"""
        from selenium.common.exceptions import NoSuchElementException
        self.mock_driver.find_element.side_effect = NoSuchElementException()
        
        result = determine_game_status(self.mock_driver, self.o_wins_board)
        self.assertEqual(result, 'lose')
    
    def test_determine_game_status_still_playing(self):
        """Test still playing status"""
        from selenium.common.exceptions import NoSuchElementException
        self.mock_driver.find_element.side_effect = NoSuchElementException()
        
        result = determine_game_status(self.mock_driver, self.ongoing_board)
        self.assertEqual(result, 'still playing')
    
    def test_determine_game_status_tie_as_still_playing(self):
        """Test tie situation returns 'still playing'"""
        from selenium.common.exceptions import NoSuchElementException
        self.mock_driver.find_element.side_effect = NoSuchElementException()
        
        result = determine_game_status(self.mock_driver, self.tie_board)
        self.assertEqual(result, 'still playing')


class TestGetCurrGameStatus(unittest.TestCase):
    """Test the main getCurrGameStatus function with mocked Selenium components"""
    
    @patch('tictactoe_tool.webdriver.Chrome')
    @patch('tictactoe_tool.WebDriverWait')
    def test_getCurrGameStatus_with_driver_creation(self, mock_wait, mock_chrome):
        """Test getCurrGameStatus when it creates its own driver"""
        # Mock driver setup
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.current_url = "about:blank"
        
        # Mock wait for element
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        
        # Mock board cells
        mock_cells = []
        board_values = ['x', 'x', 'x', 'o', 'o', '', '', '', '']  # X wins top row
        
        for i, value in enumerate(board_values):
            cell = Mock()
            cell.text = value
            mock_cells.append(cell)
        
        mock_driver.find_element.side_effect = mock_cells
        
        # Mock no game status messages (will determine from board)
        from selenium.common.exceptions import NoSuchElementException
        
        def find_element_side_effect(by, selector):
            if 'data-index' in selector:
                # Extract index from CSS selector
                import re
                match = re.search(r'data-index="(\d)"', selector)
                if match:
                    index = int(match.group(1))
                    return mock_cells[index]
            elif selector in ["congratulations", "gameStatus"]:
                raise NoSuchElementException()
            return Mock()
        
        mock_driver.find_element.side_effect = find_element_side_effect
        
        # Call the function
        result = getCurrGameStatus()
        
        # Verify results
        expected_board = [['x', 'x', 'x'], ['o', 'o', ''], ['', '', '']]
        self.assertEqual(result['currentGameBoard'], expected_board)
        self.assertEqual(result['gameStatus'], 'win')
        
        # Verify driver was created and closed
        mock_chrome.assert_called_once()
        mock_driver.quit.assert_called_once()
    
    @patch('tictactoe_tool.WebDriverWait')
    def test_getCurrGameStatus_with_provided_driver(self, mock_wait):
        """Test getCurrGameStatus with provided driver"""
        # Create mock driver
        mock_driver = Mock()
        mock_driver.current_url = "https://ttt.puppy9.com/"
        
        # Mock wait
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        
        # Mock a losing board scenario
        mock_cells = []
        board_values = ['o', 'x', 'x', 'o', 'x', 'o', 'o', '', '']  # O wins left column
        
        for value in board_values:
            cell = Mock()
            cell.text = value
            mock_cells.append(cell)
        
        # Mock congratulations element showing loss
        mock_congrats = Mock()
        mock_congrats.is_displayed.return_value = True
        mock_congrats.text = "Computer wins! Better luck next time."
        
        # Mock gameStatus element  
        mock_game_status = Mock()
        mock_game_status.text = "Computer wins! Better luck next time."
        
        def find_element_side_effect(by, selector):
            if 'data-index' in selector:
                import re
                match = re.search(r'data-index="(\d)"', selector)
                if match:
                    index = int(match.group(1))
                    return mock_cells[index]
            elif selector == "congratulations":
                return mock_congrats
            elif selector == "gameStatus":
                return mock_game_status
            return Mock()
        
        mock_driver.find_element.side_effect = find_element_side_effect
        
        # Call function with provided driver
        result = getCurrGameStatus(driver=mock_driver)
        
        # Verify results
        expected_board = [['o', 'x', 'x'], ['o', 'x', 'o'], ['o', '', '']]
        self.assertEqual(result['currentGameBoard'], expected_board)
        self.assertEqual(result['gameStatus'], 'lose')
        
        # Verify driver was not closed (since it was provided)
        mock_driver.quit.assert_not_called()
    
    @patch('tictactoe_tool.webdriver.Chrome')
    @patch('tictactoe_tool.WebDriverWait')
    def test_getCurrGameStatus_still_playing_scenario(self, mock_wait, mock_chrome):
        """Test getCurrGameStatus for ongoing game"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.current_url = "about:blank"
        
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        
        # Mock an ongoing game board
        board_values = ['x', 'o', '', '', 'x', '', 'o', '', '']
        mock_cells = []
        for value in board_values:
            cell = Mock()
            cell.text = value
            mock_cells.append(cell)
        
        from selenium.common.exceptions import NoSuchElementException
        
        def find_element_side_effect(by, selector):
            if 'data-index' in selector:
                import re
                match = re.search(r'data-index="(\d)"', selector)
                if match:
                    index = int(match.group(1))
                    return mock_cells[index]
            else:
                raise NoSuchElementException()
        
        mock_driver.find_element.side_effect = find_element_side_effect
        
        result = getCurrGameStatus()
        
        expected_board = [['x', 'o', ''], ['', 'x', ''], ['o', '', '']]
        self.assertEqual(result['currentGameBoard'], expected_board)
        self.assertEqual(result['gameStatus'], 'still playing')
    
    @patch('tictactoe_tool.webdriver.Chrome')
    @patch('tictactoe_tool.WebDriverWait')
    def test_getCurrGameStatus_handles_missing_cells(self, mock_wait, mock_chrome):
        """Test getCurrGameStatus handles missing/inaccessible cells gracefully"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.current_url = "about:blank"
        
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        
        from selenium.common.exceptions import NoSuchElementException
        
        def find_element_side_effect(by, selector):
            if 'data-index' in selector:
                # Simulate some cells being missing/inaccessible
                import re
                match = re.search(r'data-index="(\d)"', selector)
                if match:
                    index = int(match.group(1))
                    if index in [2, 5, 8]:  # Simulate missing cells
                        raise NoSuchElementException()
                    cell = Mock()
                    cell.text = 'x' if index % 2 == 0 else 'o'
                    return cell
            else:
                raise NoSuchElementException()
        
        mock_driver.find_element.side_effect = find_element_side_effect
        
        result = getCurrGameStatus()
        
        # Missing cells should be empty strings
        expected_board = [['x', 'o', ''], ['o', 'x', ''], ['x', 'o', '']]
        self.assertEqual(result['currentGameBoard'], expected_board)
        self.assertEqual(result['gameStatus'], 'still playing')


def run_specific_test():
    """Run a specific test focused on getCurrGameStatus"""
    print("=" * 60)
    print("RUNNING FOCUSED TEST FOR getCurrGameStatus")
    print("=" * 60)
    
    # Create a test suite with just the getCurrGameStatus tests
    suite = unittest.TestSuite()
    suite.addTest(TestGetCurrGameStatus('test_getCurrGameStatus_with_driver_creation'))
    suite.addTest(TestGetCurrGameStatus('test_getCurrGameStatus_with_provided_driver'))
    suite.addTest(TestGetCurrGameStatus('test_getCurrGameStatus_still_playing_scenario'))
    suite.addTest(TestGetCurrGameStatus('test_getCurrGameStatus_handles_missing_cells'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("TicTacToe Tool Test Suite")
    print("=" * 40)
    
    # Option to run focused tests or all tests
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'focus':
        success = run_specific_test()
    else:
        print("Running all tests...")
        print("Use 'python test_tictactoe_tool.py focus' to run only getCurrGameStatus tests")
        print()
        unittest.main(verbosity=2)
