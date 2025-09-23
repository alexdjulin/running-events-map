#!/usr/bin/env python3
"""
Simple FTP connection test script.
Tests if the FTP credentials in .env file are working correctly.
"""

import os
from ftplib import FTP
from dotenv import load_dotenv

def test_ftp_connection():
    """Test FTP connection using environment variables from .env file"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get FTP credentials from environment variables
    ftp_address = os.getenv('FTP_ADDRESS')
    ftp_user = os.getenv('FTP_USER')
    ftp_pwd = os.getenv('FTP_PWD')
    ftp_start_dir = os.getenv('FTP_START_DIR')
    
    # Check if all required variables are set
    if not all([ftp_address, ftp_user, ftp_pwd, ftp_start_dir]):
        print("❌ Error: Missing FTP environment variables in .env file")
        print("Required variables: FTP_ADDRESS, FTP_USER, FTP_PWD, FTP_START_DIR")
        return False
    
    print(f"Testing FTP connection to: {ftp_address}")
    print(f"Username: {ftp_user}")
    print(f"Start directory: {ftp_start_dir}")
    
    try:
        # Create FTP connection
        print("\n🔄 Connecting to FTP server...")
        ftp = FTP(ftp_address)
        
        # Login
        print("🔄 Logging in...")
        ftp.login(user=ftp_user, passwd=ftp_pwd, acct='')
        print("✅ Login successful!")
        
        # Change to start directory
        print(f"🔄 Changing to directory: {ftp_start_dir}")
        ftp.cwd(ftp_start_dir)
        print("✅ Directory change successful!")
        
        # List directory contents
        print("🔄 Listing directory contents...")
        files = []
        ftp.retrlines('LIST', files.append)
        print(f"✅ Found {len(files)} items in directory")
        
        if files:
            print("\nDirectory contents:")
            for file in files[:5]:  # Show first 5 items
                print(f"  {file}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more items")
        
        # Close connection
        ftp.quit()
        print("\n✅ FTP connection test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ FTP connection failed: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("FTP Connection Test")
    print("=" * 50)
    
    success = test_ftp_connection()
    
    if success:
        print("\n🎉 Your FTP configuration is working correctly!")
    else:
        print("\n💡 Please check your .env file and FTP credentials.")
