"""
Unit test untuk utils.parse_amount()
Jalankan dengan: python test_utils.py
"""

from utils import parse_amount, format_rupiah


def test_parse_amount():
    """Test cases untuk parse_amount"""

    print("🧪 Testing parse_amount()...\n")

    test_cases = [
        # Format dasar
        ("4000", 4000, "Angka biasa"),
        ("4k", 4000, "Format K"),
        ("4K", 4000, "Format K uppercase"),
        ("4rb", 4000, "Format rb"),
        ("4 ribu", 4000, "Format ribu dengan spasi"),
        ("4.000", 4000, "Format dengan titik"),
        ("4,000", 4000, "Format dengan koma"),
        ("4jt", 4000000, "Format juta (jt)"),
        ("4 juta", 4000000, "Format juta dengan spasi"),
        ("4m", 4000000, "Format million"),
        ("4M", 4000000, "Format million uppercase"),

        # Format penjumlahan dengan +
        ("2000 + 7000 + 8000", 17000, "Penjumlahan dengan +"),
        ("2k + 7k + 8k", 17000, "Penjumlahan K dengan +"),
        ("1jt + 500rb", 1500000, "Penjumlahan juta + ribu"),
        ("100000 + 50000 + 25000", 175000, "Penjumlahan 3 angka"),

        # Format penjumlahan dengan koma
        ("2000, 7000, 8000", 17000, "Penjumlahan dengan koma"),
        ("2k, 7k, 8k", 17000, "Penjumlahan K dengan koma"),
        ("100k, 50k, 25k", 175000, "Penjumlahan K dengan koma"),

        # Format campuran
        ("1.000.000 + 500.000", 1500000, "Penjumlahan dengan separator"),
        ("1jt + 500k + 250rb", 1750000, "Penjumlahan campuran format"),

        # Edge cases
        ("0", 0, "Angka nol"),
        ("1", 1, "Angka satu"),
        ("1k+2k+3k", 6000, "Penjumlahan tanpa spasi"),
    ]

    passed = 0
    failed = 0

    for input_str, expected, description in test_cases:
        try:
            result = parse_amount(input_str)
            if result == expected:
                print(f"✅ {description}")
                print(f"   Input: '{input_str}' → Output: {format_rupiah(result)}")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   Input: '{input_str}'")
                print(f"   Expected: {format_rupiah(expected)}, Got: {format_rupiah(result)}")
                failed += 1
        except Exception as e:
            print(f"❌ {description}")
            print(f"   Input: '{input_str}'")
            print(f"   Error: {e}")
            failed += 1
        print()

    # Test error cases
    print("\n🧪 Testing error cases...\n")

    error_cases = [
        ("", "Input kosong"),
        ("abc", "Non-numeric input"),
        ("-1000", "Angka negatif"),
        ("+++", "Hanya operator"),
    ]

    for input_str, description in error_cases:
        try:
            result = parse_amount(input_str)
            print(f"❌ {description} - Should have raised error!")
            print(f"   Input: '{input_str}' → Unexpectedly got: {result}")
            failed += 1
        except ValueError as e:
            print(f"✅ {description} - Correctly raised error")
            print(f"   Input: '{input_str}' → Error: {str(e)}")
            passed += 1
        print()

    # Summary
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Total: {passed + failed}")
    print(f"{'='*50}\n")

    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed!")

    return failed == 0


def test_format_rupiah():
    """Test cases untuk format_rupiah"""

    print("\n🧪 Testing format_rupiah()...\n")

    test_cases = [
        (1000, "Rp1.000"),
        (1234567, "Rp1.234.567"),
        (0, "Rp0"),
        (-5000, "-Rp5.000"),
        (1000000, "Rp1.000.000"),
    ]

    passed = 0
    failed = 0

    for amount, expected in test_cases:
        result = format_rupiah(amount)
        if result == expected:
            print(f"✅ {amount} → {result}")
            passed += 1
        else:
            print(f"❌ {amount} → Expected: {expected}, Got: {result}")
            failed += 1

    print(f"\n✅ Passed: {passed}/{passed + failed}\n")

    return failed == 0


def test_real_world_scenarios():
    """Test dengan skenario dunia nyata"""

    print("\n🧪 Testing real-world scenarios...\n")

    scenarios = [
        # Scenario: User input untuk /tf
        {
            "command": "/tf 2000 + 7000 + 8rb",
            "input": "2000 + 7000 + 8rb",
            "expected": 17000,
            "description": "Transfer dengan penjumlahan"
        },
        # Scenario: User input untuk /keluar
        {
            "command": "/keluar 2000 beli permen, 4000 plastik",
            "input": "2000",  # Ini yang akan di-parse sebagai amount
            "expected": 2000,
            "description": "Pengeluaran dengan keterangan (parsing pertama)"
        },
        # Scenario: User input modal
        {
            "command": "/modal 500k + 200k",
            "input": "500k + 200k",
            "expected": 700000,
            "description": "Modal dengan penjumlahan"
        },
        # Scenario: Cash akhir
        {
            "command": "/cash 1jt + 200rb + 50000",
            "input": "1jt + 200rb + 50000",
            "expected": 1250000,
            "description": "Cash dengan berbagai format"
        },
    ]

    passed = 0
    failed = 0

    for scenario in scenarios:
        print(f"📝 Scenario: {scenario['description']}")
        print(f"   Command: {scenario['command']}")

        try:
            result = parse_amount(scenario['input'])
            if result == scenario['expected']:
                print(f"   ✅ Result: {format_rupiah(result)}")
                passed += 1
            else:
                print(f"   ❌ Expected: {format_rupiah(scenario['expected'])}, Got: {format_rupiah(result)}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1

        print()

    print(f"✅ Passed: {passed}/{passed + failed}\n")

    return failed == 0


if __name__ == "__main__":
    print("="*60)
    print("🧪 UNIT TESTS - Utils Module")
    print("="*60 + "\n")

    all_passed = True

    # Run all tests
    all_passed &= test_parse_amount()
    all_passed &= test_format_rupiah()
    all_passed &= test_real_world_scenarios()

    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Please check above")
    print("="*60)
