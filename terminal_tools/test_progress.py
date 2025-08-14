"""
Tests for progress reporting functionality.

Validates ProgressReporter and ProgressManager behavior including
hierarchical progress tracking, memory integration, and positional insertion.
"""

import time
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from .progress import ProgressManager, ProgressReporter


class TestProgressReporter:
    """Test the basic ProgressReporter class."""

    def test_init(self):
        """Test ProgressReporter initialization."""
        reporter = ProgressReporter("Test Task")
        assert reporter.title == "Test Task"
        assert reporter._start_time is None
        assert reporter._last_update is None

    def test_context_manager(self):
        """Test ProgressReporter as context manager."""
        with ProgressReporter("Test") as reporter:
            assert reporter._start_time is not None
            assert isinstance(reporter._start_time, float)


class TestProgressManager(unittest.TestCase):
    """Test suite for ProgressManager functionality."""

    def setUp(self):
        """Set up a ProgressManager instance for testing."""
        self.progress_manager = ProgressManager("Test Progress")

    def test_basic_initialization(self):
        """Test ProgressManager initializes correctly."""
        self.assertEqual(self.progress_manager.title, "Test Progress")
        self.assertEqual(len(self.progress_manager.steps), 0)
        self.assertEqual(len(self.progress_manager.substeps), 0)
        self.assertEqual(len(self.progress_manager.step_order), 0)
        self.assertIsNone(self.progress_manager.active_step)
        self.assertFalse(self.progress_manager._started)

    def test_add_step_basic(self):
        """Test basic step addition functionality."""
        self.progress_manager.add_step("step1", "First Step", total=100)

        self.assertIn("step1", self.progress_manager.steps)
        self.assertEqual(self.progress_manager.steps["step1"]["title"], "First Step")
        self.assertEqual(self.progress_manager.steps["step1"]["total"], 100)
        self.assertEqual(self.progress_manager.steps["step1"]["progress"], 0)
        self.assertEqual(self.progress_manager.steps["step1"]["state"], "pending")
        self.assertEqual(self.progress_manager.step_order, ["step1"])

    def test_add_step_positional_insertion_at_end(self):
        """Test adding steps with insert_at=None (default behavior)."""
        self.progress_manager.add_step("step1", "First Step")
        self.progress_manager.add_step("step2", "Second Step")
        self.progress_manager.add_step("step3", "Third Step", insert_at=None)

        self.assertEqual(self.progress_manager.step_order, ["step1", "step2", "step3"])

    def test_add_step_positional_insertion_at_index(self):
        """Test adding steps with numeric insert_at positions."""
        self.progress_manager.add_step("step1", "First Step")
        self.progress_manager.add_step("step3", "Third Step")

        # Insert at position 1 (between step1 and step3)
        self.progress_manager.add_step("step2", "Second Step", insert_at=1)
        self.assertEqual(self.progress_manager.step_order, ["step1", "step2", "step3"])

        # Insert at position 0 (beginning)
        self.progress_manager.add_step("step0", "Zero Step", insert_at=0)
        self.assertEqual(
            self.progress_manager.step_order, ["step0", "step1", "step2", "step3"]
        )

    def test_add_step_positional_insertion_after_step(self):
        """Test adding steps with string insert_at (after named step)."""
        self.progress_manager.add_step("step1", "First Step")
        self.progress_manager.add_step("step3", "Third Step")

        # Insert after step1
        self.progress_manager.add_step("step2", "Second Step", insert_at="step1")
        self.assertEqual(self.progress_manager.step_order, ["step1", "step2", "step3"])

        # Insert after step2
        self.progress_manager.add_step("step2_5", "Step 2.5", insert_at="step2")
        self.assertEqual(
            self.progress_manager.step_order, ["step1", "step2", "step2_5", "step3"]
        )

    def test_add_step_positional_insertion_fallbacks(self):
        """Test fallback behavior for invalid insert_at values."""
        self.progress_manager.add_step("step1", "First Step")

        # Test invalid index (too large) - should fallback to append
        self.progress_manager.add_step("step2", "Second Step", insert_at=99)
        self.assertEqual(self.progress_manager.step_order, ["step1", "step2"])

        # Test negative index - should fallback to append
        self.progress_manager.add_step("step3", "Third Step", insert_at=-1)
        self.assertEqual(self.progress_manager.step_order, ["step1", "step2", "step3"])

        # Test non-existent step name - should fallback to append
        self.progress_manager.add_step("step4", "Fourth Step", insert_at="nonexistent")
        self.assertEqual(
            self.progress_manager.step_order, ["step1", "step2", "step3", "step4"]
        )

        # Test invalid type - should fallback to append
        self.progress_manager.add_step("step5", "Fifth Step", insert_at=3.14)
        self.assertEqual(
            self.progress_manager.step_order,
            ["step1", "step2", "step3", "step4", "step5"],
        )

    def test_add_substep_basic(self):
        """Test basic substep addition functionality."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep", total=50)

        self.assertIn("parent", self.progress_manager.substeps)
        self.assertIn("sub1", self.progress_manager.substeps["parent"])

        substep = self.progress_manager.substeps["parent"]["sub1"]
        self.assertEqual(substep["description"], "First substep")
        self.assertEqual(substep["total"], 50)
        self.assertEqual(substep["progress"], 0)
        self.assertEqual(substep["state"], "pending")
        self.assertEqual(substep["parent_step_id"], "parent")

    def test_add_substep_positional_insertion_at_index(self):
        """Test adding substeps with numeric insert_at positions."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep")
        self.progress_manager.add_substep("parent", "sub3", "Third substep")

        # Insert at position 1
        self.progress_manager.add_substep(
            "parent", "sub2", "Second substep", insert_at=1
        )
        substep_order = list(self.progress_manager.substeps["parent"].keys())
        self.assertEqual(substep_order, ["sub1", "sub2", "sub3"])

    def test_add_substep_positional_insertion_after_substep(self):
        """Test adding substeps with string insert_at (after named substep)."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep")
        self.progress_manager.add_substep("parent", "sub3", "Third substep")

        # Insert after sub1
        self.progress_manager.add_substep(
            "parent", "sub2", "Second substep", insert_at="sub1"
        )
        substep_order = list(self.progress_manager.substeps["parent"].keys())
        self.assertEqual(substep_order, ["sub1", "sub2", "sub3"])

    def test_add_substep_positional_insertion_fallbacks(self):
        """Test fallback behavior for invalid substep insert_at values."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep")

        # Test invalid index - should fallback to append
        self.progress_manager.add_substep(
            "parent", "sub2", "Second substep", insert_at=99
        )
        substep_order = list(self.progress_manager.substeps["parent"].keys())
        self.assertEqual(substep_order, ["sub1", "sub2"])

        # Test non-existent substep name - should fallback to append
        self.progress_manager.add_substep(
            "parent", "sub3", "Third substep", insert_at="nonexistent"
        )
        substep_order = list(self.progress_manager.substeps["parent"].keys())
        self.assertEqual(substep_order, ["sub1", "sub2", "sub3"])

    def test_add_step_duplicate_error(self):
        """Test that adding duplicate step IDs raises ValueError."""
        self.progress_manager.add_step("step1", "First Step")
        with self.assertRaises(ValueError) as context:
            self.progress_manager.add_step("step1", "Duplicate Step")
        self.assertIn("already exists", str(context.exception))

    def test_add_substep_validation_errors(self):
        """Test substep validation error handling."""
        # Test parent step not found
        with self.assertRaises(ValueError) as context:
            self.progress_manager.add_substep("nonexistent", "sub1", "Test substep")
        self.assertIn("not found", str(context.exception))

        # Test duplicate substep ID
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep")
        with self.assertRaises(ValueError) as context:
            self.progress_manager.add_substep("parent", "sub1", "Duplicate substep")
        self.assertIn("already exists", str(context.exception))

    def test_context_manager_protocol(self):
        """Test that ProgressManager supports context manager protocol."""
        with self.progress_manager as pm:
            self.assertTrue(pm._started)
            self.assertIs(pm, self.progress_manager)

        # After context exit, should be finished
        self.assertFalse(self.progress_manager._started)

    def test_display_properties(self):
        """Test display-related properties."""
        self.progress_manager.add_step("step1", "Test Step")

        with self.progress_manager:
            self.assertIsNone(self.progress_manager.live)

    def test_api_compatibility(self):
        """Test backward compatibility API methods."""
        # Test that all key methods exist and have correct signatures
        self.assertTrue(hasattr(self.progress_manager, "add_step"))
        self.assertTrue(hasattr(self.progress_manager, "add_substep"))
        self.assertTrue(hasattr(self.progress_manager, "start_step"))
        self.assertTrue(hasattr(self.progress_manager, "update_step"))
        self.assertTrue(hasattr(self.progress_manager, "complete_step"))
        self.assertTrue(hasattr(self.progress_manager, "fail_step"))
        self.assertTrue(hasattr(self.progress_manager, "start_substep"))
        self.assertTrue(hasattr(self.progress_manager, "update_substep"))
        self.assertTrue(hasattr(self.progress_manager, "complete_substep"))
        self.assertTrue(hasattr(self.progress_manager, "fail_substep"))
        self.assertTrue(hasattr(self.progress_manager, "update_step_with_memory"))
        self.assertTrue(hasattr(self.progress_manager, "display_memory_summary"))

    def test_complex_positional_insertion_scenario(self):
        """Test complex scenario with mixed positional insertions."""
        # Simulate a real-world scenario with dynamic step insertion
        self.progress_manager.add_step("load_data", "Loading data")
        self.progress_manager.add_step("analyze", "Analyzing")
        self.progress_manager.add_step("export", "Exporting results")

        # Insert preprocessing step after data loading
        self.progress_manager.add_step(
            "preprocess", "Preprocessing data", insert_at="load_data"
        )

        # Insert validation step at the beginning
        self.progress_manager.add_step("validate", "Validating inputs", insert_at=0)

        # Insert cleanup step at end
        self.progress_manager.add_step("cleanup", "Cleaning up")

        expected_order = [
            "validate",
            "load_data",
            "preprocess",
            "analyze",
            "export",
            "cleanup",
        ]
        self.assertEqual(self.progress_manager.step_order, expected_order)

        # Add substeps with positional insertion
        self.progress_manager.add_substep("preprocess", "filter", "Filtering data")
        self.progress_manager.add_substep("preprocess", "normalize", "Normalizing data")
        self.progress_manager.add_substep(
            "preprocess", "validate_schema", "Validating schema", insert_at="filter"
        )

        substep_order = list(self.progress_manager.substeps["preprocess"].keys())
        expected_substeps = ["filter", "validate_schema", "normalize"]
        self.assertEqual(substep_order, expected_substeps)

    def test_memory_manager_integration(self):
        """Test ProgressManager integration with memory manager."""
        # Test with mock memory manager
        from unittest.mock import Mock

        mock_memory_manager = Mock()

        pm_with_memory = ProgressManager(
            "Test with Memory", memory_manager=mock_memory_manager
        )
        self.assertEqual(pm_with_memory.memory_manager, mock_memory_manager)
        self.assertIsNotNone(pm_with_memory.last_memory_warning)

    def test_table_rebuild_functionality(self):
        """Test table rebuilding with positional insertion."""
        self.progress_manager.add_step("step1", "First Step")
        self.progress_manager.add_step("step2", "Second Step")

        self.progress_manager._rebuild_table()
        self.assertIsNotNone(self.progress_manager.table)

        self.progress_manager.add_substep("step1", "sub1", "Substep 1")
        self.progress_manager._rebuild_table()
        self.assertIsNotNone(self.progress_manager.table)


class TestProgressManagerPositionalInsertion(unittest.TestCase):
    """Test positional insertion edge cases and advanced scenarios."""

    def setUp(self):
        self.pm = ProgressManager("Positional Insertion Tests")

    def test_insertion_at_boundary_conditions(self):
        """Test insertion at boundary conditions (0, exact length)."""
        self.pm.add_step("middle", "Middle Step")

        # Insert at beginning (index 0)
        self.pm.add_step("first", "First Step", insert_at=0)
        self.assertEqual(self.pm.step_order, ["first", "middle"])

        # Insert at exact length (should append)
        self.pm.add_step("last", "Last Step", insert_at=2)
        self.assertEqual(self.pm.step_order, ["first", "middle", "last"])

    def test_insertion_preserves_existing_data(self):
        """Test that insertions don't corrupt existing step data."""
        self.pm.add_step("step1", "Step 1", total=100)
        self.pm.add_step("step3", "Step 3", total=300)

        # Insert between existing steps
        self.pm.add_step("step2", "Step 2", total=200, insert_at=1)

        # Verify all step data is preserved
        self.assertEqual(self.pm.steps["step1"]["total"], 100)
        self.assertEqual(self.pm.steps["step2"]["total"], 200)
        self.assertEqual(self.pm.steps["step3"]["total"], 300)
        self.assertEqual(self.pm.step_order, ["step1", "step2", "step3"])

    def test_substep_insertion_with_multiple_parents(self):
        """Test substep insertion works correctly with multiple parent steps."""
        self.pm.add_step("parent1", "Parent 1")
        self.pm.add_step("parent2", "Parent 2")

        # Add substeps to both parents
        self.pm.add_substep("parent1", "p1_sub1", "P1 Sub 1")
        self.pm.add_substep("parent1", "p1_sub3", "P1 Sub 3")
        self.pm.add_substep("parent2", "p2_sub1", "P2 Sub 1")

        # Insert substep in parent1
        self.pm.add_substep("parent1", "p1_sub2", "P1 Sub 2", insert_at=1)

        # Verify parent1 substeps are correctly ordered
        p1_order = list(self.pm.substeps["parent1"].keys())
        self.assertEqual(p1_order, ["p1_sub1", "p1_sub2", "p1_sub3"])

        # Verify parent2 is unaffected
        p2_order = list(self.pm.substeps["parent2"].keys())
        self.assertEqual(p2_order, ["p2_sub1"])

    def test_performance_with_many_insertions(self):
        """Test that positional insertion performs reasonably with many steps."""
        import time

        start_time = time.time()

        # Add many steps with various insertion patterns
        for i in range(100):
            if i % 3 == 0:
                self.pm.add_step(
                    f"step_{i}", f"Step {i}", insert_at=0
                )  # Insert at beginning
            elif i % 3 == 1:
                self.pm.add_step(f"step_{i}", f"Step {i}")  # Append at end
            else:
                self.pm.add_step(
                    f"step_{i}", f"Step {i}", insert_at=len(self.pm.step_order) // 2
                )  # Insert at middle

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in reasonable time (less than 1 second for 100 insertions)
        self.assertLess(execution_time, 1.0)
        self.assertEqual(len(self.pm.step_order), 100)

    def test_insertion_with_unicode_and_special_characters(self):
        """Test insertion works with unicode and special characters in IDs and titles."""
        self.pm.add_step("step_1", "Step 1")
        self.pm.add_step("étape_2", "Étape avec accents", insert_at="step_1")
        self.pm.add_step("шаг_3", "Шаг на русском языке")
        self.pm.add_step("步骤_4", "中文步骤", insert_at=1)

        # Verify order and that unicode is handled correctly
        expected_order = ["step_1", "步骤_4", "étape_2", "шаг_3"]
        self.assertEqual(self.pm.step_order, expected_order)


if __name__ == "__main__":
    unittest.main()
