"""
Quick configuration script for Vusion Manager Pro API - Sweden Lab
Stores the API key securely for elkjop_se_lab.
"""

from vusion_api_config import VusionAPIConfig


def main():
    print()
    print("=" * 80)
    print("Vusion Manager Pro API Key Configuration - Sweden Lab")
    print("=" * 80)
    print()
    print("This script will securely store your Vusion Manager Pro API key for Sweden.")
    print("The key will be encrypted and saved to your home directory.")
    print()
    print("Store: elkjop_se_lab.lab5")
    print("Country: SE (Sweden)")
    print("Service: Vusion Manager Pro")
    print()
    print("-" * 80)
    print()
    
    # Get API key from user
    api_key = input("Enter your Vusion Manager Pro API key: ").strip()
    
    if not api_key:
        print()
        print("❌ No API key entered. Exiting.")
        print()
        return
    
    print()
    print("Saving API key...")
    
    try:
        config = VusionAPIConfig()
        config.set_api_key('SE', 'vusion_pro', api_key)
        
        print()
        print("✓ API key saved successfully!")
        print()
        print(f"Configuration file: {config.config_file}")
        print(f"Encryption key file: {config.key_file}")
        print()
        print("-" * 80)
        print()
        print("Next steps:")
        print("  1. Run: python test_elkjop_se_lab.py")
        print("  2. Verify the connection works")
        print("  3. Check that store and gateway data is retrieved")
        print()
        print("The API is now ready to use in the AP Panel!")
        print()
        
    except Exception as e:
        print()
        print(f"❌ Error saving API key: {e}")
        print()
        return


if __name__ == '__main__':
    main()
