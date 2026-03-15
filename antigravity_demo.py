"""
ANTIGRAVITY EASTER EGG DEMONSTRATION
=====================================

This script demonstrates the Python antigravity Easter egg.
As required for the GitHub Peru Analytics project, run this first!

When you run `import antigravity`, Python will open your web browser
to the XKCD comic #353 about Python.

Take a screenshot of the comic in your browser and save it to:
demo/antigravity_screenshot.png
"""

import webbrowser
import time

def show_antigravity():
    """
    Demonstrate the antigravity Easter egg.
    """
    print("=" * 70)
    print("GITHUB PERU ANALYTICS - ANTIGRAVITY EASTER EGG")
    print("=" * 70)
    print()
    print("🐍 Python's antigravity module is one of the fun Easter eggs!")
    print("📖 It references XKCD comic #353: 'Python'")
    print()
    print("   The comic shows:")
    print("   'I just learned about Python. Flying is easy!'")
    print("   *person flies away*")
    print()
    print("🚀 Running import antigravity...")
    print()
    
    # Give user time to read
    time.sleep(2)
    
    try:
        # This will open the XKCD comic in your default browser
        import antigravity
        
        print("✅ SUCCESS! Your browser should now show the XKCD comic.")
        print()
        print("📸 IMPORTANT: Take a screenshot of the comic!")
        print("   Save it as: demo/antigravity_screenshot.png")
        print()
        print("=" * 70)
        print("Why this matters:")
        print("- Shows Python's fun, welcoming culture")
        print("- Easter eggs make programming enjoyable")
        print("- Required for project submission! 😊")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Opening XKCD comic manually...")
        webbrowser.open("https://xkcd.com/353/")


if __name__ == "__main__":
    show_antigravity()
    
    # Wait for user to see the comic
    input("\nPress Enter after you've taken your screenshot...")
    
    print()
    print("Great! Now you're ready to start your GitHub Peru Analytics project! 🇵🇪")
    print()
    print("Next steps:")
    print("1. Set up your .env file with GitHub and OpenAI tokens")
    print("2. Run: python scripts/extract_data.py")
    print("3. Run: python scripts/classify_repos.py")
    print("4. Run: streamlit run app/main.py")
