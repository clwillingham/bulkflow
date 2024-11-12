import os
from typing import Dict, List
from .processors import ImportManager, CSVProcessor
from .database import PostgresLoader
from .utils.logging_config import setup_logging

def preview_data(csv_processor: CSVProcessor) -> bool:
    """Preview data and get user confirmation"""
    print("\nPreviewing first few rows of data:")
    print("-" * 80)
    preview_rows = csv_processor.preview_data(5)
    if preview_rows:
        # Print header
        print("Header:", ", ".join(preview_rows[0]))
        print("\nSample rows:")
        for row in preview_rows[1:]:
            print(row)
    print("-" * 80)
    
    # Ask for confirmation before proceeding
    response = input("\nDoes the data look correct? (yes/no): ")
    return response.lower() == 'yes'

def process_file(file_path: str, db_params: Dict[str, str], table_name: str):
    """Main function to process and load the file"""
    logger = setup_logging(__name__)
    
    # Initialize managers
    import_manager = ImportManager(file_path)
    csv_processor = CSVProcessor(import_manager)
    
    # Preview and confirm data format
    if not preview_data(csv_processor):
        print("Import cancelled by user")
        return
    
    postgres_loader = PostgresLoader(import_manager, db_params, table_name)
    
    try:
        # Process and load the file in chunks
        for position, chunk, is_first_chunk in csv_processor.process_csv_in_chunks():
            success = postgres_loader.copy_to_postgres(position, chunk, is_first_chunk)
            
            if not success:
                import_manager.logger.error(f"Failed to process chunk at position {position}")
                continue
        
        # After completion, provide detailed summary
        if import_manager.state.failed_chunks or os.path.getsize(import_manager.state.failed_rows_file) > 0:
            with open(import_manager.state.failed_rows_file, 'r') as f:
                failed_rows_count = sum(1 for line in f) - 1  # Subtract header row
            
            import_manager.logger.warning(
                f"Import completed with the following issues:\n"
                f"- {len(import_manager.state.failed_chunks)} failed chunks\n"
                f"- {failed_rows_count} failed rows\n"
                f"Failed rows have been logged to: {import_manager.state.failed_rows_file}\n"
                f"Run again to retry failed chunks, or process failed rows separately using the failed rows file."
            )
        else:
            import_manager.logger.info("Import completed successfully with no errors!")
            
    except KeyboardInterrupt:
        import_manager.logger.info("Process interrupted. Progress saved. Run again to resume.")
    except Exception as e:
        import_manager.logger.error(f"Fatal error: {e}")
        raise
    finally:
        import_manager.save_state()

if __name__ == '__main__':
    # Configuration
    db_params = {
        'dbname': 'your_database',
        'user': 'your_username',
        'password': 'your_password',
        'host': 'your_host',
        'port': '5432'
    }
    
    file_path = 'sample.csv'
    table_name = 'import.sample'
    
    process_file(file_path, db_params, table_name)
