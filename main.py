"""
Software Version Management System
Main entry point with numbered menu navigation

This application demonstrates mastery of Python concepts:
- Real-life context: Software version tracking for DevOps
- Modular design with feature-specific modules
- Data structures (dictionaries, lists, nested structures)
- File I/O with CSV
- Input validation
- Functions with parameters and returns
- Loops (for and while)
"""

import csv_manager
import display_data


def initialize_data():
    """
    Initialize data structures before displaying the main menu.
    Ensures CSV file exists with default values if not present.
    Returns the initialized version data.
    """
    # This will create the CSV with defaults if it doesn't exist
    versions = csv_manager.load_installed_versions()
    
    return versions


def display_main_menu():
    """
    Display the main menu options.
    This function only displays the menu, not processing input.
    """
    print("\n" + "="*70)
    print("SOFTWARE VERSION MANAGEMENT SYSTEM")
    print("="*70)
    print("\n1. Display installed versions")
    print("2. Update versions")
    print("3. Exit")
    print("="*70)


def main():
    """
    Main function - entry point of the application.
    Displays numbered menu and routes to appropriate modules.
    Runs in a loop until user selects Exit.
    No feature logic belongs here - only navigation.
    """
    # Initialize data structures before main menu
    initialize_data()
    
    # Main menu loop - continues until user exits
    while True:
        display_main_menu()
        
        try:
            # Get user choice with validation
            choice = input("\nEnter your choice (1-3): ").strip()
            
            # Route to appropriate module based on choice
            if choice == '1':
                # Display installed versions
                display_data.show_all_components()
                input("\nPress Enter to continue...")
            
            elif choice == '2':
                # Update versions (module handles sub-menu for manual/CSV)
                display_data.enter_desired_versions()
            
            elif choice == '3':
                # Exit the program
                print("\n" + "="*70)
                print("Thank you for using Software Version Management System!")
                print("="*70)
                break
            
            else:
                # Invalid input handling
                print("\n⚠ Invalid choice. Please enter a number between 1 and 3.")
        
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\nProgram interrupted. Exiting...")
            break
        
        except Exception as e:
            # Catch any unexpected errors
            print(f"\n⚠ An error occurred: {e}")
            print("Please try again or contact support if the problem persists.")


# Entry point - only runs when this file is executed directly
if __name__ == "__main__":
    try:
        # Start the main program directly
        main()
    
    except Exception as e:
        print(f"\nFatal error: {e}")
        print("The program will now exit.")
