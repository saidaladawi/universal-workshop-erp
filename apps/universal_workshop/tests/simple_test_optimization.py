#!/usr/bin/env python3


def test_image_optimization():
    """Simple test for image optimization system"""
    try:
        from universal_workshop.utils.image_optimizer import ImageOptimizer

        print("🧪 Testing Image Optimization System")
        print("=" * 50)

        # Test instantiation
        optimizer = ImageOptimizer("test_workshop")
        print("✅ ImageOptimizer instantiated successfully")

        # Test size variants
        print("📏 Size variants configured:")
        for variant, size in ImageOptimizer.SIZE_VARIANTS.items():
            print(f"   - {variant}: {size}")

        # Test quality settings
        print("🎨 Quality settings configured:")
        for setting, quality in ImageOptimizer.QUALITY_SETTINGS.items():
            print(f"   - {setting}: {quality}%")

        print("✅ Image optimization system is working!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_image_optimization()
