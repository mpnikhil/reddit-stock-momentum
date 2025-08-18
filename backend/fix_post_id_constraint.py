#!/usr/bin/env python3
"""
Fix post_id constraint in stock_mentions table
The post_id should be nullable for comment mentions
"""

import sqlite3
import os
from datetime import datetime

def fix_post_id_constraint(db_path):
    """Make post_id nullable in stock_mentions table"""
    
    print(f"🔄 Fixing post_id constraint in: {db_path}")
    
    # Backup first
    backup_path = f"{db_path}.backup_constraint_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current constraint
        cursor.execute("PRAGMA table_info(stock_mentions)")
        columns = cursor.fetchall()
        
        print("Current schema:")
        for col in columns:
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"  {col[1]} ({col[2]}) {nullable}")
        
        # Check if post_id is nullable
        post_id_info = [col for col in columns if col[1] == 'post_id'][0]
        is_nullable = post_id_info[3] == 0  # 0 means nullable
        
        if is_nullable:
            print("✅ post_id is already nullable!")
            conn.close()
            return True
        
        print("🔧 Making post_id nullable...")
        
        # SQLite doesn't support modifying column constraints directly
        # We need to recreate the table
        
        # Create new table with nullable post_id
        cursor.execute("""
            CREATE TABLE stock_mentions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id VARCHAR,  -- Made nullable
                comment_id VARCHAR,
                stock_symbol VARCHAR NOT NULL,
                mention_count INTEGER DEFAULT 1,
                sentiment_score FLOAT,
                context_snippet TEXT,
                source_type VARCHAR DEFAULT 'post',
                created_at DATETIME,
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (comment_id) REFERENCES comments(id),
                FOREIGN KEY (stock_symbol) REFERENCES stocks(symbol)
            )
        """)
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO stock_mentions_new 
            SELECT * FROM stock_mentions
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE stock_mentions")
        cursor.execute("ALTER TABLE stock_mentions_new RENAME TO stock_mentions")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_stock_created ON stock_mentions(stock_symbol, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_post_stock ON stock_mentions(post_id, stock_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_comment_stock ON stock_mentions(comment_id, stock_symbol)")
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(stock_mentions)")
        new_columns = cursor.fetchall()
        
        print("\nUpdated schema:")
        for col in new_columns:
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"  {col[1]} ({col[2]}) {nullable}")
        
        post_id_new = [col for col in new_columns if col[1] == 'post_id'][0]
        if post_id_new[3] == 0:  # 0 means nullable
            print("✅ post_id is now nullable!")
            
            # Test count
            cursor.execute("SELECT COUNT(*) FROM stock_mentions")
            count = cursor.fetchone()[0]
            print(f"✅ Preserved {count} existing stock mentions")
            
            conn.close()
            return True
        else:
            print("❌ Failed to make post_id nullable")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error fixing constraint: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def main():
    db_path = "data/reddit_stocks.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🔧 Fixing post_id constraint in stock_mentions table")
    print("=" * 60)
    
    success = fix_post_id_constraint(db_path)
    
    if success:
        print("\n🎉 Constraint fix completed successfully!")
        print("Now comment mentions can be saved without requiring a post_id")
    else:
        print("\n💥 Constraint fix failed!")

if __name__ == "__main__":
    main()
