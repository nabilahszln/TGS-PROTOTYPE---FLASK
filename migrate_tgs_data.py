#!/usr/bin/env python3
"""
Data Migration Script for TGS Resolution History
Converts old CSV format to new format with updated status terminology
"""

import pandas as pd
import os
from datetime import datetime

def clean_text_encoding(text):
    """Clean text from encoding issues"""
    if not text or pd.isna(text):
        return text
    
    # Convert to string and clean encoding issues
    text = str(text)
    text = text.replace('Ã¢â‚¬Â¢', '')  # Remove bullet encoding
    text = text.replace('Ã¢â‚¬"', '-')   # Replace em dash
    text = text.replace('Ã¢â‚¬â„¢', "'")  # Replace apostrophe
    text = text.replace('Ã¢â‚¬Å"', '"')   # Replace left quote
    text = text.replace('Ã¢â‚¬', '"')     # Replace right quote
    text = text.replace('Ã‚', '')        # Remove non-breaking space
    text = text.replace('â€¢', '')       # Remove bullet points
    text = text.replace('â€"', '-')      # Replace em dash
    text = text.replace('â€™', "'")      # Replace right single quote
    text = text.replace('â€œ', '"')      # Replace left double quote
    text = text.replace('â€', '"')       # Replace right double quote
    
    # Clean multiple spaces and trim
    text = ' '.join(text.split())
    return text.strip()

def migrate_tgs_data():
    """Main migration function"""
    old_filename = "tgs_resolution_history.csv"
    new_filename = "tgs_resolution_history_v2.csv"
    backup_filename = f"tgs_resolution_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    print("🔄 TGS Data Migration Starting...")
    print("=" * 50)
    
    # Check if old file exists
    if not os.path.exists(old_filename):
        print(f"❌ Old file '{old_filename}' not found.")
        return False
    
    # Check if new file already exists
    if os.path.exists(new_filename):
        print(f"⚠️  New file '{new_filename}' already exists.")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled.")
            return False
    
    try:
        # Load old data
        print(f"📖 Loading data from '{old_filename}'...")
        df = pd.read_csv(old_filename)
        original_count = len(df)
        print(f"📊 Found {original_count} records")
        
        # Create backup
        print(f"💾 Creating backup as '{backup_filename}'...")
        df.to_csv(backup_filename, index=False)
        
        # Update status column
        if 'Status' in df.columns:
            print("🔄 Updating status terminology...")
            status_mapping = {
                "Resolved": "Non-Relevant Failure",
                "Failed": "Relevant Failure"
            }
            
            before_counts = df['Status'].value_counts()
            print("📊 Before migration:")
            for status, count in before_counts.items():
                print(f"   {status}: {count}")
            
            df['Status'] = df['Status'].map(status_mapping).fillna(df['Status'])
            
            after_counts = df['Status'].value_counts()
            print("📊 After migration:")
            for status, count in after_counts.items():
                print(f"   {status}: {count}")
        
        # Clean text columns
        print("🧹 Cleaning text encoding issues...")
        text_columns = ['Equipment', 'Failure Scenario', 'Guideline for Chief Controller', 'Local Response']
        cleaned_count = 0
        
        for col in text_columns:
            if col in df.columns:
                print(f"   Cleaning column: {col}")
                original_data = df[col].copy()
                df[col] = df[col].apply(clean_text_encoding)
                
                # Count how many entries were cleaned
                changes = sum(original_data != df[col])
                if changes > 0:
                    cleaned_count += changes
                    print(f"     ✅ Cleaned {changes} entries")
        
        print(f"🧹 Total text entries cleaned: {cleaned_count}")
        
        # Save new file
        print(f"💾 Saving migrated data to '{new_filename}'...")
        df.to_csv(new_filename, index=False)
        
        # Verify migration
        verification_df = pd.read_csv(new_filename)
        if len(verification_df) == original_count:
            print("✅ Migration completed successfully!")
            print(f"📁 Files created:")
            print(f"   - New data: {new_filename}")
            print(f"   - Backup: {backup_filename}")
            print(f"   - Original: {old_filename} (unchanged)")
            
            print("\n📋 Migration Summary:")
            print("   ✅ Status terminology updated:")
            print("      'Resolved' → 'Non-Relevant Failure'")
            print("      'Failed' → 'Relevant Failure'")
            print("   ✅ Text encoding issues cleaned")
            print("   ✅ Data integrity maintained")
            
            return True
        else:
            print("❌ Verification failed - record count mismatch!")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def show_status_explanation():
    """Show explanation of new status terminology"""
    print("\n📖 New Status Terminology Explanation:")
    print("=" * 45)
    print("🟢 Non-Relevant Failure:")
    print("   - Issue resolved within 5 minutes")
    print("   - Quick resolution achieved")
    print("   - Previously called 'Resolved'")
    print()
    print("🔴 Relevant Failure:")
    print("   - Issue took more than 5 minutes to resolve")
    print("   - Exceeded target resolution time")
    print("   - Previously called 'Failed'")
    print()
    print("⏱️  The 5-minute threshold determines relevance")
    print("   based on operational efficiency standards.")

if __name__ == "__main__":
    print("TGS Resolution History Migration Tool")
    print("=" * 40)
    
    # Show explanation first
    show_status_explanation()
    
    # Confirm migration
    print("\n🚀 Ready to migrate data?")
    response = input("Continue with migration? (y/N): ")
    
    if response.lower() == 'y':
        success = migrate_tgs_data()
        if success:
            print("\n🎉 Migration completed successfully!")
            print("You can now use the new data format in your application.")
        else:
            print("\n💥 Migration failed. Please check the errors above.")
    else:
        print("Migration cancelled by user.")
    
    print("\nPress Enter to exit...")
    input()