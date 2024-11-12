# BulkFlow

A high-performance Python package for efficiently loading large CSV datasets into PostgreSQL databases. Features chunked processing, automatic resume capability, and comprehensive error handling.

## Key Features

- 🚀 **High Performance**: Optimized chunk-based processing for handling large datasets efficiently
- 🔄 **Resume Capability**: Automatically resume interrupted imports from the last successful position
- 🛡️ **Error Resilience**: Comprehensive error handling with detailed logging and failed row tracking
- 🔍 **Data Validation**: Preview data before import and validate row structure
- 📊 **Progress Tracking**: Real-time progress updates with ETA and processing speed
- 🔄 **Duplicate Handling**: Smart handling of duplicate records
- 🔌 **Connection Pooling**: Efficient database connection management
- 📝 **Detailed Logging**: Comprehensive logging of all operations and errors

## Installation

```bash
pip install bulkflow
```

## Quick Start

1. Create a database configuration file (`db_config.json`):
```json
{
    "dbname": "your_database",
    "user": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": "5432"
}
```

2. Run the import:
```bash
bulkflow path/to/your/file.csv your_table_name
```

## Project Structure

```
bulkflow/
├── src/
│   ├── models/          # Data models
│   ├── processors/      # Core processing logic
│   ├── database/        # Database operations
│   └── utils/          # Utility functions
```

## Usage Examples

### Basic Usage

```python
from bulkflow import process_file

db_config = {
    "dbname": "your_database",
    "user": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": "5432"
}

process_file(file_path, db_config, table_name)
```

### CLI Usage

```bash
# Basic usage
bulkflow data.csv target_table

# Custom config file
bulkflow data.csv target_table --config my_config.json
```

## Error Handling

BulkFlow provides comprehensive error handling:

1. **Failed Rows File**: `failed_rows_YYYYMMDD_HHMMSS.csv`
   - Records individual row failures
   - Includes row number, content, error reason, and timestamp

2. **Import State File**: `import_state.json`
   - Tracks overall import progress
   - Enables resume capability
   - Records failed chunk information

## Performance Optimization

BulkFlow automatically optimizes performance by:

- Calculating optimal chunk sizes based on available memory
- Using connection pooling for database operations
- Implementing efficient duplicate handling strategies
- Minimizing memory usage through streaming processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for robust, production-ready data import solutions
- Built with modern Python best practices
- Designed for real-world use cases and large-scale data processing

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/clwillingham/bulkflow/issues) page
2. Create a new issue if your problem isn't already listed
3. Provide as much context as possible in your issue description
4. Try to fix the issue yourself and submit a Pull Request if you can

## Author

Created and maintained by [Chris Willingham](https://github.com/clwillingham)

## AI Contribution

The majority of this project's code was generated using AI assistance, specifically:
- [Cline](https://github.com/cline/cline) - AI coding assistant
- Claude 3.5 Sonnet (new) - Large language model by Anthropic
