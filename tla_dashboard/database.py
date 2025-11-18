"""
database.py - Modular DuckDB Database Manager for Job Scraping

This module provides a scalable database interface for storing LinkedIn job data
with support for hirer information, applications, and form submissions.
"""

import duckdb
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages DuckDB database connections and schema operations.
    Designed for scalability and modularity for job scraping applications.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the database directory. If None, uses default location.
        """
        if db_path is None:
            # Default path: root_folder/database/jobs.duckdb
            root = Path(__file__).parent.parent
            self.db_dir = root / "database"
        else:
            self.db_dir = Path(db_path)
        
        # Ensure directory exists
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.db_dir / "jobs.duckdb"
        
        logger.info(f"Database initialized at: {self.db_file}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection handling and cleanup.
        
        Usage:
            with db_manager.get_connection() as conn:
                conn.execute("SELECT * FROM jobs")
        """
        conn = duckdb.connect(str(self.db_file))
        try:
            yield conn
        finally:
            conn.close()
    
    def initialize_schema(self):
        """
        Create all database tables with optimized schema for job listings.
        Uses sequences for auto-incrementing primary keys.
        """
        with self.get_connection() as conn:
            # Create sequences for auto-incrementing IDs
            conn.execute("CREATE SEQUENCE IF NOT EXISTS jobs_id_seq START 1")
            conn.execute("CREATE SEQUENCE IF NOT EXISTS hirers_id_seq START 1")
            conn.execute("CREATE SEQUENCE IF NOT EXISTS sessions_id_seq START 1")
            conn.execute("CREATE SEQUENCE IF NOT EXISTS history_id_seq START 1")
            
            # Main jobs table with auto-incrementing ID
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY DEFAULT nextval('jobs_id_seq'),
                    job_id VARCHAR UNIQUE NOT NULL,
                    job_link VARCHAR,
                    title VARCHAR NOT NULL,
                    company VARCHAR,
                    location VARCHAR,
                    description TEXT,
                    hirer_name VARCHAR,
                    hirer_profile_link VARCHAR,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR DEFAULT 'active',
                    is_applied BOOLEAN DEFAULT false
                )
            """)
            
            # Hirers/Recruiters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hirers (
                    id INTEGER PRIMARY KEY DEFAULT nextval('hirers_id_seq'),
                    hirer_name VARCHAR NOT NULL,
                    hirer_profile_link VARCHAR UNIQUE,
                    company VARCHAR,
                    jobs_posted INTEGER DEFAULT 0,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # Scraping sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    session_id INTEGER PRIMARY KEY DEFAULT nextval('sessions_id_seq'),
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    jobs_found INTEGER DEFAULT 0,
                    jobs_new INTEGER DEFAULT 0,
                    jobs_updated INTEGER DEFAULT 0,
                    search_query VARCHAR,
                    status VARCHAR DEFAULT 'in_progress',
                    error_log TEXT,
                    metadata JSON
                )
            """)
            
            # Job history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_history (
                    history_id INTEGER PRIMARY KEY DEFAULT nextval('history_id_seq'),
                    job_id VARCHAR NOT NULL,
                    field_name VARCHAR NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Core schema initialized successfully")

    
    def add_application_tables(self):
        """
        Add tables for tracking job applications and form submissions.
        """
        with self.get_connection() as conn:
            # Create sequences for application tables
            conn.execute("CREATE SEQUENCE IF NOT EXISTS applications_id_seq START 1")
            conn.execute("CREATE SEQUENCE IF NOT EXISTS questions_id_seq START 1")
            conn.execute("CREATE SEQUENCE IF NOT EXISTS responses_id_seq START 1")
            conn.execute("CREATE SEQUENCE IF NOT EXISTS documents_id_seq START 1")
            
            # Applications table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    application_id INTEGER PRIMARY KEY DEFAULT nextval('applications_id_seq'),
                    job_id VARCHAR NOT NULL,
                    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR DEFAULT 'submitted',
                    application_method VARCHAR,
                    confirmation_number VARCHAR,
                    response_received BOOLEAN DEFAULT false,
                    response_date TIMESTAMP,
                    response_details TEXT,
                    notes TEXT
                )
            """)
            
            # Form questions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS form_questions (
                    question_id INTEGER PRIMARY KEY DEFAULT nextval('questions_id_seq'),
                    job_id VARCHAR,
                    question_text TEXT NOT NULL,
                    question_type VARCHAR,
                    is_required BOOLEAN DEFAULT false,
                    options JSON,
                    display_order INTEGER,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Form responses table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS form_responses (
                    response_id INTEGER PRIMARY KEY DEFAULT nextval('responses_id_seq'),
                    application_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    response_value TEXT,
                    response_data JSON,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Application documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS application_documents (
                    document_id INTEGER PRIMARY KEY DEFAULT nextval('documents_id_seq'),
                    application_id INTEGER NOT NULL,
                    document_type VARCHAR,
                    file_name VARCHAR,
                    file_path VARCHAR,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Application tracking tables created successfully")
    
    def create_indexes(self):
        """
        Create indexes after bulk loading data.
        Per DuckDB best practices, indexes should be added after data loading.
        """
        with self.get_connection() as conn:
            # Jobs table indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_job_id 
                ON jobs(job_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_company 
                ON jobs(company)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at 
                ON jobs(scraped_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status 
                ON jobs(status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_is_applied 
                ON jobs(is_applied)
            """)
            
            # Hirers table indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hirers_profile_link 
                ON hirers(hirer_profile_link)
            """)
            
            # Applications table indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_applications_job_id 
                ON applications(job_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_applications_status 
                ON applications(status)
            """)
            
            logger.info("Indexes created successfully")
    
    def insert_job(self, job_data: Dict[str, Any]) -> int:
        """
        Insert a single job into the database.
        
        Args:
            job_data: Dictionary containing job fields from get_job_info()
            
        Returns:
            ID of the inserted record, or None if job_id already exists
        """
        with self.get_connection() as conn:
            # Check if job already exists
            existing = conn.execute(
                "SELECT id FROM jobs WHERE job_id = ?",
                [job_data.get('job_id')]
            ).fetchone()
            
            if existing:
                logger.info(f"Job {job_data.get('job_id')} already exists, skipping")
                return existing[0]
            
            result = conn.execute("""
                INSERT INTO jobs 
                (job_id, job_link, title, company, location, description, 
                 hirer_name, hirer_profile_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, [
                job_data.get('job_id'),
                job_data.get('job_link'),
                job_data.get('title'),
                job_data.get('company'),
                job_data.get('location'),
                job_data.get('description'),
                job_data.get('hirer_name'),
                job_data.get('hirer_profile_link')
            ]).fetchone()
            
            logger.info(f"Inserted job: {job_data.get('title')} at {job_data.get('company')}")
            return result[0] if result else None
    
    def bulk_insert_jobs(self, jobs_list: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple jobs at once for better performance.
        
        Args:
            jobs_list: List of job dictionaries from get_job_info()
            
        Returns:
            Number of jobs inserted
        """
        with self.get_connection() as conn:
            # Prepare data for bulk insert
            values = [
                (
                    job.get('job_id'),
                    job.get('job_link'),
                    job.get('title'),
                    job.get('company'),
                    job.get('location'),
                    job.get('description'),
                    job.get('hirer_name'),
                    job.get('hirer_profile_link')
                )
                for job in jobs_list
            ]
            
            # Use executemany for bulk insert
            conn.executemany("""
                INSERT INTO jobs 
                (job_id, job_link, title, company, location, description, 
                 hirer_name, hirer_profile_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (job_id) DO NOTHING
            """, values)
            
            inserted_count = len(values)
            logger.info(f"Bulk inserted {inserted_count} jobs")
            return inserted_count
    
    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """
        Update an existing job record.
        
        Args:
            job_id: The job_id to update
            updates: Dictionary of field names and new values
        """
        with self.get_connection() as conn:
            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [job_id]
            
            conn.execute(f"""
                UPDATE jobs 
                SET {set_clause}, last_updated = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """, values)
            
            logger.info(f"Updated job {job_id}")
    
    def mark_as_applied(self, job_id: str, application_data: Optional[Dict[str, Any]] = None):
        """
        Mark a job as applied and optionally create application record.
        
        Args:
            job_id: The job_id to mark as applied
            application_data: Optional application details
        """
        with self.get_connection() as conn:
            # Update job status
            conn.execute("""
                UPDATE jobs 
                SET is_applied = true, last_updated = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """, [job_id])
            
            # Create application record if data provided
            if application_data:
                conn.execute("""
                    INSERT INTO applications 
                    (job_id, application_method, confirmation_number, notes)
                    VALUES (?, ?, ?, ?)
                """, [
                    job_id,
                    application_data.get('application_method'),
                    application_data.get('confirmation_number'),
                    application_data.get('notes')
                ])
            
            logger.info(f"Marked job {job_id} as applied")
    
    def get_unapplied_jobs(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all jobs that haven't been applied to yet.
        
        Args:
            limit: Optional limit on number of results
            
        Returns:
            List of job dictionaries
        """
        with self.get_connection() as conn:
            query = """
                SELECT job_id, title, company, location, job_link, 
                       hirer_name, description, scraped_at
                FROM jobs 
                WHERE is_applied = false AND status = 'active'
                ORDER BY scraped_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            results = conn.execute(query).fetchall()
            
            # Convert to list of dictionaries
            columns = ['job_id', 'title', 'company', 'location', 'job_link', 
                      'hirer_name', 'description', 'scraped_at']
            return [dict(zip(columns, row)) for row in results]
    
    def search_jobs(self, search_term: str, field: str = 'title') -> List[Dict]:
        """
        Search for jobs by a specific field.
        
        Args:
            search_term: Term to search for
            field: Field to search in (title, company, location, description)
            
        Returns:
            List of matching job dictionaries
        """
        with self.get_connection() as conn:
            query = f"""
                SELECT job_id, title, company, location, job_link, description
                FROM jobs 
                WHERE {field} ILIKE ?
                ORDER BY scraped_at DESC
            """
            
            results = conn.execute(query, [f'%{search_term}%']).fetchall()
            
            columns = ['job_id', 'title', 'company', 'location', 'job_link', 'description']
            return [dict(zip(columns, row)) for row in results]
    
    def get_jobs_by_company(self, company_name: str) -> List[Dict]:
        """
        Get all jobs from a specific company.
        
        Args:
            company_name: Company name to filter by
            
        Returns:
            List of job dictionaries
        """
        return self.search_jobs(company_name, field='company')
    
    def start_scraping_session(self, search_query: Optional[str] = None, 
                              metadata: Optional[Dict] = None) -> int:
        """
        Start a new scraping session and return its ID.
        
        Args:
            search_query: The search query used for this session
            metadata: Additional metadata as JSON
            
        Returns:
            Session ID
        """
        with self.get_connection() as conn:
            result = conn.execute("""
                INSERT INTO scraping_sessions (search_query, metadata)
                VALUES (?, ?)
                RETURNING session_id
            """, [search_query, metadata]).fetchone()
            
            return result[0] if result else None
    
    def end_scraping_session(self, session_id: int, jobs_found: int = 0, 
                            jobs_new: int = 0, error_log: Optional[str] = None):
        """
        End a scraping session and update statistics.
        
        Args:
            session_id: The session ID to end
            jobs_found: Total jobs found
            jobs_new: Number of new jobs added
            error_log: Any errors encountered
        """
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE scraping_sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    jobs_found = ?,
                    jobs_new = ?,
                    status = 'completed',
                    error_log = ?
                WHERE session_id = ?
            """, [jobs_found, jobs_new, error_log, session_id])
            
            logger.info(f"Session {session_id} completed: {jobs_new} new jobs")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with various statistics
        """
        with self.get_connection() as conn:
            stats = {}
            
            # Total jobs
            stats['total_jobs'] = conn.execute(
                "SELECT COUNT(*) FROM jobs"
            ).fetchone()[0]
            
            # Applied jobs
            stats['applied_jobs'] = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE is_applied = true"
            ).fetchone()[0]
            
            # Unapplied jobs
            stats['unapplied_jobs'] = stats['total_jobs'] - stats['applied_jobs']
            
            # Unique companies
            stats['unique_companies'] = conn.execute(
                "SELECT COUNT(DISTINCT company) FROM jobs"
            ).fetchone()[0]
            
            # Jobs by company (top 10)
            stats['top_companies'] = conn.execute("""
                SELECT company, COUNT(*) as job_count
                FROM jobs
                WHERE company IS NOT NULL
                GROUP BY company
                ORDER BY job_count DESC
                LIMIT 10
            """).fetchall()
            
            # Recent scraping sessions
            stats['last_session'] = conn.execute("""
                SELECT session_id, start_time, jobs_found, status
                FROM scraping_sessions
                ORDER BY start_time DESC
                LIMIT 1
            """).fetchone()
            
            return stats
    
    def export_to_csv(self, table_name: str, output_path: str):
        """
        Export a table to CSV file.
        
        Args:
            table_name: Name of the table to export
            output_path: Path for the output CSV file
        """
        with self.get_connection() as conn:
            conn.execute(f"""
                COPY {table_name} TO '{output_path}' (HEADER, DELIMITER ',')
            """)
            logger.info(f"Exported {table_name} to {output_path}")
    
    def import_from_csv(self, table_name: str, csv_path: str):
        """
        Import data from CSV file into a table.
        
        Args:
            table_name: Target table name
            csv_path: Path to CSV file
        """
        with self.get_connection() as conn:
            conn.execute(f"""
                COPY {table_name} FROM '{csv_path}' (HEADER, DELIMITER ',')
            """)
            logger.info(f"Imported data from {csv_path} into {table_name}")
    
    def execute_query(self, query: str, params: Optional[List] = None):
        """
        Execute a custom SQL query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Query results
        """
        with self.get_connection() as conn:
            if params:
                return conn.execute(query, params).fetchall()
            return conn.execute(query).fetchall()
    
    def get_table_info(self, table_name: str):
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table schema information
        """
        with self.get_connection() as conn:
            return conn.execute(f"DESCRIBE {table_name}").fetchall()
    
    def vacuum_database(self):
        """
        Optimize database by checkpointing and reclaiming space.
        """
        with self.get_connection() as conn:
            conn.execute("CHECKPOINT")
            logger.info("Database optimized")
    def save_application_qna(self, job_id: str, qa: dict, application_method: str = "easy_apply", notes: str = None) -> dict:
        """
        Persist a simple dict of {question_text: response} for a given job_id.
        - Creates (or reuses) an application row for this job_id.
        - Upserts each question into form_questions (scoped by job_id).
        - Inserts a response row for each question for this application.
        
        Args:
            job_id: External job identifier (matches jobs.job_id)
            qa: Dict mapping question_text -> response (str | dict | list | None)
            application_method: How the application was made (e.g., 'easy_apply')
            notes: Optional notes to store on the application
        
        Returns:
            Dict with keys:
                application_id: int
                questions_upserted: int
                responses_inserted: int
        """
        if not job_id:
            raise ValueError("job_id is required")
        if not isinstance(qa, dict) or not qa:
            raise ValueError("qa must be a non-empty dict of {question_text: response}")
        
        # Normalizer: split response into response_value (display string) and response_data (JSON)
        def split_response(resp):
            # If scalar, store as response_value; if complex, store as JSON
            if resp is None:
                return None, None
            if isinstance(resp, (str, int, float, bool)):
                return str(resp), None
            # list/dict/other → put into response_data JSON, keep a short display value
            try:
                # Short readable display value
                display = None
                if isinstance(resp, list):
                    display = ", ".join([str(x) for x in resp[:5]]) + ("..." if len(resp) > 5 else "")
                elif isinstance(resp, dict):
                    # Show first 3 key:val pairs as preview
                    items = list(resp.items())[:3]
                    display = ", ".join([f"{k}: {v}" for k, v in items])
                else:
                    display = str(resp)
                return display, resp
            except Exception:
                return None, None
        
        with self.get_connection() as conn:
            # Begin transaction
            conn.execute("BEGIN")
            try:
                # 1) Create or reuse application
                existing = conn.execute("""
                    SELECT application_id 
                    FROM applications 
                    WHERE job_id = ? 
                    ORDER BY applied_date DESC 
                    LIMIT 1
                """, [job_id]).fetchone()
                
                if existing:
                    application_id = existing[0]
                else:
                    application_id = conn.execute("""
                        INSERT INTO applications (job_id, status, application_method, notes)
                        VALUES (?, 'submitted', ?, ?)
                        RETURNING application_id
                    """, [job_id, application_method, notes]).fetchone()[0]
                
                questions_upserted = 0
                responses_inserted = 0
                
                for question_text, resp in qa.items():
                    if not question_text or not isinstance(question_text, str):
                        continue  # skip invalid question text
                    
                    # 2) Upsert question (scope by job_id + question_text)
                    row = conn.execute("""
                        SELECT question_id 
                        FROM form_questions 
                        WHERE job_id IS NOT DISTINCT FROM ? 
                        AND question_text = ?
                        LIMIT 1
                    """, [job_id, question_text]).fetchone()
                    
                    if row:
                        question_id = row[0]
                    else:
                        question_id = conn.execute("""
                            INSERT INTO form_questions (job_id, question_text, question_type, is_required, options, display_order)
                            VALUES (?, ?, NULL, false, NULL, NULL)
                            RETURNING question_id
                        """, [job_id, question_text]).fetchone()[0]
                        questions_upserted += 1
                    
                    # 3) Insert response
                    response_value, response_data = split_response(resp)
                    conn.execute("""
                        INSERT INTO form_responses (application_id, question_id, response_value, response_data)
                        VALUES (?, ?, ?, ?)
                    """, [application_id, question_id, response_value, response_data])
                    responses_inserted += 1
                
                # Commit transaction
                conn.execute("COMMIT")
                return {
                    "application_id": application_id,
                    "questions_upserted": questions_upserted,
                    "responses_inserted": responses_inserted
                }
            except Exception as e:
                conn.execute("ROLLBACK")
                raise
    def finalize_application(self, job_id: str, application_id: int, confirmation_number: str | None = None, response_details: str | None = None) -> None:
        """
        Mark an application as successfully submitted and toggle the job's is_applied flag.
        Runs in a single transaction for consistency.

        Args:
            job_id: External job identifier (jobs.job_id)
            application_id: The applications.application_id to finalize
            confirmation_number: Optional confirmation/tracking number captured after submit
            response_details: Optional free-text details from the submission (e.g., success message)

        Effects:
            - jobs.is_applied = TRUE, jobs.last_updated = CURRENT_TIMESTAMP
            - applications.status = 'submitted', response_received = TRUE, response_date = CURRENT_TIMESTAMP
            - applications.confirmation_number / response_details updated if provided
        """
        if not job_id:
            raise ValueError("job_id is required")
        if not application_id:
            raise ValueError("application_id is required")

        with self.get_connection() as conn:
            conn.execute("BEGIN")
            try:
                # 1) Toggle the job flag
                conn.execute("""
                    UPDATE jobs
                    SET is_applied = TRUE,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                """, [job_id])

                # 2) Update application status and metadata
                conn.execute("""
                    UPDATE applications
                    SET status = 'submitted',
                        response_received = TRUE,
                        response_date = CURRENT_TIMESTAMP,
                        confirmation_number = COALESCE(?, confirmation_number),
                        response_details = COALESCE(?, response_details)
                    WHERE application_id = ?
                """, [confirmation_number, response_details, application_id])

                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise



# Convenience function for quick setup
def setup_database(db_path: Optional[str] = None, 
                   include_applications: bool = False) -> DatabaseManager:
    """
    Initialize and set up the database with default schema.
    
    Args:
        db_path: Optional custom database path
        include_applications: Whether to create application tracking tables
        
    Returns:
        Configured DatabaseManager instance
    """
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_schema()
    
    if include_applications:
        db_manager.add_application_tables()
    
    return db_manager


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = setup_database()
    
    # Example: Insert sample job data (matching your scraper output)
    sample_job = {
        'job_id': '12345678',
        'job_link': 'https://www.linkedin.com/jobs/view/12345678',
        'title': 'Senior Python Developer',
        'company': 'Tech Corp',
        'location': 'San Francisco, CA',
        'description': 'We are looking for an experienced Python developer...',
        'hirer_name': 'John Doe',
        'hirer_profile_link': 'https://www.linkedin.com/in/johndoe'
    }
    
    job_id = db.insert_job(sample_job)
    print(f"Inserted job with ID: {job_id}")
    
    # Get unapplied jobs
    unapplied = db.get_unapplied_jobs(limit=5)
    print(f"\nFound {len(unapplied)} unapplied jobs")
    
    # Show statistics
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"Total Jobs: {stats['total_jobs']}")
    print(f"Unapplied Jobs: {stats['unapplied_jobs']}")
    
    # Show table structure
    print("\nJobs Table Schema:")
    for row in db.get_table_info('jobs'):
        print(row)
