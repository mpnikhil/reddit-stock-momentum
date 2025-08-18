#!/usr/bin/env python3
"""
Database Migration Script
Adds missing columns to stock_mentions table to support comment processing
"""

import sqlite3
import os
import sys
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database before migration"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Copy database file
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return None

def check_current_schema(cursor):
    """Check the current schema of stock_mentions table"""
    cursor.execute("PRAGMA table_info(stock_mentions)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print("Current stock_mentions table schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    return column_names

def migrate_stock_mentions_table(db_path):
    """Migrate the stock_mentions table to add missing columns"""
    
    print(f"🔄 Starting database migration for: {db_path}")
    
    # Backup first
    backup_path = backup_database(db_path)
    if not backup_path:
        print("❌ Migration aborted - could not create backup")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        current_columns = check_current_schema(cursor)
        
        # Check if migration is needed
        needs_migration = False
        missing_columns = []
        
        if 'comment_id' not in current_columns:
            missing_columns.append('comment_id')
            needs_migration = True
            
        if 'source_type' not in current_columns:
            missing_columns.append('source_type')
            needs_migration = True
        
        if not needs_migration:
            print("✅ Database schema is already up to date!")
            conn.close()
            return True
        
        print(f"🔧 Adding missing columns: {missing_columns}")
        
        # Add missing columns
        if 'comment_id' in missing_columns:
            cursor.execute("ALTER TABLE stock_mentions ADD COLUMN comment_id VARCHAR")
            print("  ✅ Added comment_id column")
        
        if 'source_type' in missing_columns:
            cursor.execute("ALTER TABLE stock_mentions ADD COLUMN source_type VARCHAR DEFAULT 'post'")
            print("  ✅ Added source_type column")
        
        # Update existing records to have source_type = 'post'
        cursor.execute("UPDATE stock_mentions SET source_type = 'post' WHERE source_type IS NULL")
        updated_rows = cursor.rowcount
        print(f"  ✅ Updated {updated_rows} existing records with source_type = 'post'")
        
        # Create indexes for the new columns
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_comment_stock ON stock_mentions(comment_id, stock_symbol)")
            print("  ✅ Created index for comment_id + stock_symbol")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not create index: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        print("\n🔍 Verifying migration...")
        new_columns = check_current_schema(cursor)
        
        if 'comment_id' in new_columns and 'source_type' in new_columns:
            print("✅ Migration completed successfully!")
            
            # Show updated stats
            cursor.execute("SELECT COUNT(*) FROM stock_mentions")
            total_mentions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM stock_mentions WHERE source_type = 'post'")
            post_mentions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM stock_mentions WHERE source_type = 'comment'")
            comment_mentions = cursor.fetchone()[0]
            
            print(f"\n📊 Current stock mentions:")
            print(f"  Total: {total_mentions}")
            print(f"  From posts: {post_mentions}")
            print(f"  From comments: {comment_mentions}")
            
            conn.close()
            return True
        else:
            print("❌ Migration verification failed!")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def main():
    """Main migration function"""
    db_path = "backend/data/reddit_stocks.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    print("🚀 Reddit Scraper Database Migration")
    print("=" * 50)
    
    success = migrate_stock_mentions_table(db_path)
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart the backend server")
        print("2. Trigger comment processing to analyze existing comments")
        print("3. Monitor logs for comment stock mention extraction")
    else:
        print("\n💥 Migration failed!")
        print("Check the backup file and logs for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()
