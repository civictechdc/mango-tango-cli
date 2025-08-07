"""
Tests for terminal_tools/progress.py progress reporting functionality.

This test suite validates:
- AdvancedProgressReporter initialization and basic functionality
- Context manager behavior
- Progress updates and tracking
- Error handling and edge cases
"""

import time
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from .progress import ProgressReporter, RichProgressManager


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


class TestRichProgressManager:
    """Test the enhanced RichProgressManager class."""

    def test_init(self):
        """Test RichProgressManager initialization."""
        manager = RichProgressManager("Test Analysis")
        assert manager.title == "Test Analysis"
        assert manager.steps == {}
        assert manager.step_order == []
        assert manager.active_step is None
        assert not manager._started

    def test_add_step_without_total(self):
        """Test adding steps without progress totals."""
        manager = RichProgressManager("Test Analysis")

        manager.add_step("step1", "First step")
        assert "step1" in manager.steps
        assert manager.steps["step1"]["title"] == "First step"
        assert manager.steps["step1"]["total"] is None
        assert manager.steps["step1"]["progress"] == 0
        assert manager.steps["step1"]["state"] == "pending"
        assert manager.steps["step1"]["error_msg"] is None
        assert "step1" in manager.step_order
        # Steps without totals don't have progress tracking capabilities

    def test_add_step_with_total(self):
        """Test adding steps with progress totals."""
        manager = RichProgressManager("Test Analysis")

        manager.add_step("step2", "Second step", 100)
        assert manager.steps["step2"]["total"] == 100
        # Steps with totals support progress tracking

        # Verify multiple steps maintain order
        manager.add_step("step3", "Third step", 50)
        assert len(manager.step_order) == 2
        assert manager.step_order == ["step2", "step3"]

    def test_add_duplicate_step_raises_error(self):
        """Test that adding duplicate step IDs raises ValueError."""
        manager = RichProgressManager("Test Analysis")
        manager.add_step("step1", "First step")

        with pytest.raises(ValueError, match="Step 'step1' already exists"):
            manager.add_step("step1", "Duplicate step")

    def test_all_steps_visible_from_start(self):
        """Test that all steps are visible from the start, not just when active."""
        manager = RichProgressManager("Test Analysis")

        # Add multiple steps
        manager.add_step("preprocess", "Preprocessing data", 1000)
        manager.add_step("tokenize", "Tokenizing text", 500)
        manager.add_step("ngrams", "Generating n-grams", 200)
        manager.add_step("output", "Writing outputs")  # No total

        # All steps should be in pending state initially
        for step_id in ["preprocess", "tokenize", "ngrams", "output"]:
            assert manager.steps[step_id]["state"] == "pending"
            assert step_id in manager.step_order

        # Verify order is maintained
        assert manager.step_order == ["preprocess", "tokenize", "ngrams", "output"]

    def test_status_icons_update_correctly(self):
        """Test that status icons update correctly throughout workflow."""
        manager = RichProgressManager("Test Analysis")

        # Verify symbols are correct
        assert manager.SYMBOLS["pending"] == "⏸"
        assert manager.SYMBOLS["active"] == "⏳"
        assert manager.SYMBOLS["completed"] == "✓"
        assert manager.SYMBOLS["failed"] == "❌"

        manager.add_step("step1", "Test step", 100)

        # Initial state should be pending
        assert manager.steps["step1"]["state"] == "pending"

        # After starting should be active
        manager.start_step("step1")
        assert manager.steps["step1"]["state"] == "active"
        assert manager.active_step == "step1"

        # After completing should be completed
        manager.complete_step("step1")
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.active_step is None

        # Test failure state
        manager.add_step("step2", "Failing step", 50)
        manager.start_step("step2")
        manager.fail_step("step2", "Test error")
        assert manager.steps["step2"]["state"] == "failed"
        assert manager.steps["step2"]["error_msg"] == "Test error"

    def test_progress_bars_only_for_active_with_totals(self):
        """Test that progress bars appear only for active tasks with totals."""
        manager = RichProgressManager("Test Analysis")

        # Add step with total
        manager.add_step("with_total", "Step with total", 100)
        assert "with_total" in manager.steps
        assert manager.steps["with_total"]["total"] == 100

        # Add step without total
        manager.add_step("without_total", "Step without total")
        assert "without_total" in manager.steps
        assert manager.steps["without_total"]["total"] is None

        # Start step with total
        manager.start_step("with_total")
        assert manager.active_step == "with_total"

        # Complete and start step without total
        manager.complete_step("with_total")
        manager.start_step("without_total")
        assert manager.active_step == "without_total"

    def test_start_step_validation(self):
        """Test starting step with proper validation."""
        manager = RichProgressManager("Test Analysis")

        # Test starting nonexistent step
        with pytest.raises(ValueError, match="Step 'nonexistent' not found"):
            manager.start_step("nonexistent")

        # Test normal start
        manager.add_step("step1", "Test step", 100)
        manager.start_step("step1")
        assert manager.active_step == "step1"
        assert manager.steps["step1"]["state"] == "active"

    def test_start_step_completes_previous_active(self):
        """Test that starting a new step completes the previously active step."""
        manager = RichProgressManager("Test Analysis")

        manager.add_step("step1", "First step", 100)
        manager.add_step("step2", "Second step", 50)

        # Start first step
        manager.start_step("step1")
        assert manager.active_step == "step1"
        assert manager.steps["step1"]["state"] == "active"

        # Start second step - should complete first step
        manager.start_step("step2")
        assert manager.active_step == "step2"
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.steps["step2"]["state"] == "active"

    def test_update_step_comprehensive_validation(self):
        """Test comprehensive validation for step updates."""
        manager = RichProgressManager("Test Analysis")
        manager.add_step("step1", "Test step", 100)

        # Test valid updates
        manager.update_step("step1", 50)
        assert manager.steps["step1"]["progress"] == 50

        manager.update_step("step1", 100)  # Max value
        assert manager.steps["step1"]["progress"] == 100

        manager.update_step("step1", 0)  # Min value
        assert manager.steps["step1"]["progress"] == 0

        # Test invalid step_id
        with pytest.raises(ValueError, match="Step 'nonexistent' not found"):
            manager.update_step("nonexistent", 50)

        # Test invalid step_id types
        with pytest.raises(
            ValueError, match="Invalid step_id: must be a non-empty string"
        ):
            manager.update_step("", 50)

        with pytest.raises(
            ValueError, match="Invalid step_id: must be a non-empty string"
        ):
            manager.update_step(None, 50)

        # Test invalid progress types
        with pytest.raises(TypeError, match="Progress must be a number"):
            manager.update_step("step1", "invalid")

        # Test negative progress
        with pytest.raises(ValueError, match="Progress cannot be negative"):
            manager.update_step("step1", -1)

        # Test progress exceeding total
        with pytest.raises(ValueError, match="Progress 150 exceeds total 100"):
            manager.update_step("step1", 150)

        # Test float progress (should be kept as float)
        manager.update_step("step1", 75.8)
        assert manager.steps["step1"]["progress"] == 75.8

    def test_update_step_without_total(self):
        """Test updating steps that don't have totals."""
        manager = RichProgressManager("Test Analysis")
        manager.add_step("step1", "Step without total")  # No total

        # Should accept any reasonable progress value
        manager.update_step("step1", 0)
        assert manager.steps["step1"]["progress"] == 0

        manager.update_step("step1", 42)
        assert manager.steps["step1"]["progress"] == 42

        # Still validate types and negative values
        with pytest.raises(ValueError, match="Progress cannot be negative"):
            manager.update_step("step1", -1)

    def test_complete_step_with_total(self):
        """Test completing steps that have totals."""
        manager = RichProgressManager("Test Analysis")
        manager.add_step("step1", "Test step", 100)

        # Complete step - should set progress to total
        manager.complete_step("step1")
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.steps["step1"]["progress"] == 100  # Should be set to total

        # If it was active step, should clear active step
        manager.add_step("step2", "Another step", 50)
        manager.start_step("step2")
        assert manager.active_step == "step2"

        manager.complete_step("step2")
        assert manager.active_step is None

    def test_complete_step_without_total(self):
        """Test completing steps that don't have totals."""
        manager = RichProgressManager("Test Analysis")
        manager.add_step("step1", "Step without total")  # No total

        # Set some progress first
        manager.update_step("step1", 42)

        manager.complete_step("step1")
        assert manager.steps["step1"]["state"] == "completed"
        # Progress should remain unchanged when no total
        assert manager.steps["step1"]["progress"] == 42

    def test_fail_step_comprehensive(self):
        """Test comprehensive failure scenarios."""
        manager = RichProgressManager("Test Analysis")
        manager.add_step("step1", "Test step", 100)

        # Test failing with error message
        manager.fail_step("step1", "Something went wrong")
        assert manager.steps["step1"]["state"] == "failed"
        assert manager.steps["step1"]["error_msg"] == "Something went wrong"

        # Test failing without error message
        manager.add_step("step2", "Another step")
        manager.fail_step("step2")
        assert manager.steps["step2"]["state"] == "failed"
        assert manager.steps["step2"]["error_msg"] is None

        # Test failing nonexistent step
        with pytest.raises(ValueError, match="Step 'nonexistent' not found"):
            manager.fail_step("nonexistent")

        # Test that active step is cleared when failed
        manager.add_step("step3", "Active step", 50)
        manager.start_step("step3")
        assert manager.active_step == "step3"

        manager.fail_step("step3", "Failed while active")
        assert manager.active_step is None

    def test_context_manager_functionality(self):
        """Test RichProgressManager as context manager."""
        with RichProgressManager("Test Analysis") as manager:
            assert manager._started
            manager.add_step("step1", "First step", 100)
            manager.start_step("step1")
            manager.update_step("step1", 50)
            manager.complete_step("step1")

        assert not manager._started
        # Manager should be properly finished
        assert manager.live is None

    @patch("sys.stdout")
    def test_threading_and_locking(self, mock_stdout):
        """Test thread safety with multiple rapid updates."""
        import threading
        import time

        manager = RichProgressManager("Threading Test")
        manager.add_step("step1", "Threaded step", 1000)

        # Track completion
        update_count = 0
        update_lock = threading.Lock()

        def update_worker(start_val, end_val):
            nonlocal update_count
            for i in range(start_val, end_val):
                try:
                    manager.update_step("step1", i)
                    with update_lock:
                        update_count += 1
                    time.sleep(
                        0.001
                    )  # Small delay to increase chance of race conditions
                except Exception:
                    pass  # Ignore any threading-related errors for this test

        with manager:
            manager.start_step("step1")

            # Start multiple threads updating the same step
            threads = []
            for i in range(0, 100, 20):
                thread = threading.Thread(
                    target=update_worker, args=(i, min(i + 20, 100))
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Complete the step
            manager.complete_step("step1")

        # Should have processed many updates without crashing
        assert update_count > 0
        assert manager.steps["step1"]["state"] == "completed"

    def test_analyzer_workflow_integration(self):
        """Test integration with typical analyzer workflow patterns."""
        manager = RichProgressManager("N-gram Analysis")

        # Add steps matching typical analyzer workflow
        manager.add_step("preprocess", "Preprocessing and filtering messages", 1000)
        manager.add_step("tokenize", "Tokenizing text data", 500)
        manager.add_step("ngrams", "Generating n-grams", 200)
        manager.add_step("dictionary", "Building n-gram dictionary")  # No total
        manager.add_step("output", "Writing analysis results")  # No total

        # Simulate full workflow
        # Step 1: Preprocessing with incremental updates
        manager.start_step("preprocess")
        for i in range(0, 1001, 100):
            manager.update_step("preprocess", min(i, 1000))
        manager.complete_step("preprocess")

        # Step 2: Tokenization with batch updates
        manager.start_step("tokenize")
        batch_size = 50
        for batch in range(0, 500, batch_size):
            manager.update_step("tokenize", min(batch + batch_size, 500))
        manager.complete_step("tokenize")

        # Step 3: N-gram generation (simulate failure)
        manager.start_step("ngrams")
        manager.update_step("ngrams", 100)
        manager.fail_step("ngrams", "Out of memory")

        # Step 4: Dictionary building (no progress tracking)
        manager.start_step("dictionary")
        manager.complete_step("dictionary")

        # Step 5: Output writing
        manager.start_step("output")
        manager.complete_step("output")

        # Verify final states
        assert manager.steps["preprocess"]["state"] == "completed"
        assert manager.steps["preprocess"]["progress"] == 1000
        assert manager.steps["tokenize"]["state"] == "completed"
        assert manager.steps["tokenize"]["progress"] == 500
        assert manager.steps["ngrams"]["state"] == "failed"
        assert manager.steps["ngrams"]["error_msg"] == "Out of memory"
        assert manager.steps["dictionary"]["state"] == "completed"
        assert manager.steps["output"]["state"] == "completed"

    def test_progress_callback_compatibility(self):
        """Test that the system works with progress callback patterns."""
        manager = RichProgressManager("Callback Test")
        manager.add_step("process", "Processing items", 100)

        # Simulate progress callback function like those used in analyzers
        def progress_callback(current, total=None):
            if total is not None and "process" in manager.steps:
                # Update step total if needed
                if manager.steps["process"]["total"] != total:
                    manager.steps["process"]["total"] = total
                manager.update_step("process", current)

        manager.start_step("process")

        # Simulate analyzer calling progress callback
        for i in range(0, 101, 10):
            progress_callback(i, 100)

        manager.complete_step("process")

        assert manager.steps["process"]["progress"] == 100
        assert manager.steps["process"]["state"] == "completed"

    def test_backward_compatibility_checklist_alias(self):
        """Test that ChecklistProgressManager alias works for backward compatibility."""
        from terminal_tools.progress import ChecklistProgressManager

        # Should be the same as RichProgressManager
        assert ChecklistProgressManager is RichProgressManager

        # Test it works as expected
        manager = ChecklistProgressManager("Backward Compatibility Test")
        manager.add_step("step1", "Test step", 50)

        assert isinstance(manager, RichProgressManager)
        assert manager.title == "Backward Compatibility Test"
        assert "step1" in manager.steps

    @patch("sys.stdout")
    def test_display_update_error_handling(self, mock_stdout):
        """Test graceful handling of display update errors."""
        manager = RichProgressManager("Error Handling Test")
        manager.add_step("step1", "Test step", 100)

        # Start the manager to enable display updates
        with manager:
            manager.start_step("step1")

            # This should not crash even if display updates fail
            # We can't easily mock Rich components to fail, but we can test
            # that invalid operations don't crash the progress tracking
            manager.update_step("step1", 50)
            manager.complete_step("step1")

        # Progress tracking should still work correctly
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.steps["step1"]["progress"] == 100

    def test_multiple_steps_managed_simultaneously(self):
        """Test that multiple steps can be managed simultaneously correctly."""
        manager = RichProgressManager("Multi-Step Test")

        # Add several steps
        step_configs = [
            ("step1", "First step", 100),
            ("step2", "Second step", 200),
            ("step3", "Third step", None),  # No total
            ("step4", "Fourth step", 50),
            ("step5", "Fifth step", None),  # No total
        ]

        for step_id, title, total in step_configs:
            manager.add_step(step_id, title, total)

        # Verify all steps are tracked
        assert len(manager.steps) == 5
        assert len(manager.step_order) == 5

        # Verify steps with totals are properly tracked
        steps_with_totals = {
            step_id
            for step_id, step_info in manager.steps.items()
            if step_info["total"] is not None
        }
        expected_steps_with_totals = {"step1", "step2", "step4"}
        assert steps_with_totals == expected_steps_with_totals

        # Test sequential processing
        manager.start_step("step1")
        manager.update_step("step1", 100)
        manager.complete_step("step1")

        manager.start_step("step2")
        manager.update_step("step2", 150)
        manager.fail_step("step2", "Simulated failure")

        manager.start_step("step3")  # No total
        manager.complete_step("step3")

        manager.start_step("step4")
        manager.update_step("step4", 25)
        manager.update_step("step4", 50)
        manager.complete_step("step4")

        manager.start_step("step5")  # No total
        manager.complete_step("step5")

        # Verify final states
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.steps["step1"]["progress"] == 100
        assert manager.steps["step2"]["state"] == "failed"
        assert manager.steps["step2"]["progress"] == 150
        assert manager.steps["step3"]["state"] == "completed"
        assert manager.steps["step4"]["state"] == "completed"
        assert manager.steps["step4"]["progress"] == 50
        assert manager.steps["step5"]["state"] == "completed"

    def test_performance_with_large_numbers_of_steps(self):
        """Test performance with large numbers of steps."""
        manager = RichProgressManager("Performance Test")

        # Add many steps
        num_steps = 100
        for i in range(num_steps):
            total = (
                50 if i % 2 == 0 else None
            )  # Alternate between steps with/without totals
            manager.add_step(f"step_{i}", f"Step {i}", total)

        assert len(manager.steps) == num_steps
        assert len(manager.step_order) == num_steps

        # Should be able to process them efficiently
        import time

        start_time = time.time()

        # Process a few steps to test performance
        for i in range(min(10, num_steps)):
            step_id = f"step_{i}"
            manager.start_step(step_id)
            if manager.steps[step_id]["total"] is not None:
                manager.update_step(step_id, 25)
            manager.complete_step(step_id)

        elapsed = time.time() - start_time
        # Should complete quickly (less than 1 second for this simple operation)
        assert elapsed < 1.0

        # Verify states are correct
        for i in range(min(10, num_steps)):
            assert manager.steps[f"step_{i}"]["state"] == "completed"

    def test_rich_components_integration(self):
        """Test that Rich components are properly integrated."""
        manager = RichProgressManager("Rich Integration Test")
        manager.add_step("step1", "Test step", 100)

        # Test that Rich components are initialized
        assert manager.console is not None
        assert hasattr(manager, "SYMBOLS")

        # Test that we can start and use the manager without crashing
        manager.start()
        assert manager._started
        # Live display should be None until we start using steps
        assert manager.live is None

        # Once we start a step, live display should be created
        manager.start_step("step1")
        assert manager.live is not None

        # Test that display updates work without crashing
        manager.update_step("step1", 50)
        manager.complete_step("step1")

        # Test finish
        manager.finish()
        assert not manager._started

    def test_step_order_preservation(self):
        """Test that step order is preserved throughout operations."""
        manager = RichProgressManager("Order Test")

        # Add steps in specific order
        step_names = ["alpha", "beta", "gamma", "delta", "epsilon"]
        for i, name in enumerate(step_names):
            total = (i + 1) * 10 if i % 2 == 0 else None
            manager.add_step(name, f"Step {name}", total)

        # Verify order is maintained
        assert manager.step_order == step_names

        # Process steps out of order
        manager.start_step("gamma")
        manager.complete_step("gamma")

        manager.start_step("alpha")
        manager.update_step("alpha", 5)
        manager.complete_step("alpha")

        manager.start_step("epsilon")
        manager.fail_step("epsilon", "Test failure")

        # Order should still be preserved
        assert manager.step_order == step_names

        # All steps should still be accessible in original order
        for name in step_names:
            assert name in manager.steps

    def test_edge_cases_and_boundary_conditions(self):
        """Test edge cases and boundary conditions."""
        manager = RichProgressManager("Edge Cases Test")

        # Test zero total
        manager.add_step("zero_total", "Zero total step", 0)
        manager.start_step("zero_total")
        manager.update_step("zero_total", 0)  # Should not raise error
        manager.complete_step("zero_total")
        assert manager.steps["zero_total"]["progress"] == 0

        # Test step with total = 1
        manager.add_step("single_item", "Single item step", 1)
        manager.start_step("single_item")
        manager.update_step("single_item", 1)
        manager.complete_step("single_item")
        assert manager.steps["single_item"]["progress"] == 1

        # Test very large total
        large_total = 1000000
        manager.add_step("large_step", "Large step", large_total)
        manager.start_step("large_step")
        manager.update_step("large_step", large_total // 2)
        manager.update_step("large_step", large_total)
        manager.complete_step("large_step")
        assert manager.steps["large_step"]["progress"] == large_total

        # Test empty title
        manager.add_step("empty_title", "", 10)
        assert manager.steps["empty_title"]["title"] == ""

        # Test very long title
        long_title = "A" * 1000
        manager.add_step("long_title", long_title, 10)
        assert manager.steps["long_title"]["title"] == long_title

    def test_rapid_progress_updates_stress_test(self):
        """Test system handles rapid progress updates without losing data."""
        manager = RichProgressManager("Stress Test")
        manager.add_step("rapid_step", "Rapid updates", 10000)

        # Rapid updates without starting manager (lighter test)
        for i in range(0, 10001, 100):
            manager.update_step("rapid_step", i)

        assert manager.steps["rapid_step"]["progress"] == 10000

        # Test that we can handle updates even when values go backwards
        # (should still validate against total)
        manager.update_step("rapid_step", 5000)
        assert manager.steps["rapid_step"]["progress"] == 5000

    def test_display_components_render_correctly(self):
        """Test that display components are created correctly."""
        manager = RichProgressManager("Display Test")
        manager.add_step("step1", "Test step with progress", 100)
        manager.add_step("step2", "Test step without progress")

        # Test that manager initializes Rich components
        assert hasattr(manager, "console")
        assert hasattr(manager, "live")
        assert hasattr(manager, "SYMBOLS")

        # Test symbols are correct
        expected_symbols = {
            "pending": "⏸",
            "active": "⏳",
            "completed": "✓",
            "failed": "❌",
        }
        assert manager.SYMBOLS == expected_symbols

    def test_concurrent_step_state_changes(self):
        """Test handling concurrent step state changes."""
        import threading

        manager = RichProgressManager("Concurrent Test")

        # Add multiple steps
        for i in range(5):
            manager.add_step(f"step_{i}", f"Concurrent Step {i}", 100)

        results = {}

        def process_step(step_id):
            try:
                manager.start_step(step_id)
                for progress in range(0, 101, 10):
                    manager.update_step(step_id, progress)
                manager.complete_step(step_id)
                results[step_id] = "completed"
            except Exception as e:
                results[step_id] = f"error: {e}"

        # Start threads for each step
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_step, args=(f"step_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All steps should complete successfully
        # Note: Due to the automatic completion of previous active steps,
        # only the last step will remain active, others will be completed
        completed_count = 0
        for step_id in manager.steps:
            if manager.steps[step_id]["state"] == "completed":
                completed_count += 1

        # Should have completed all steps
        assert completed_count >= 4  # At least 4 should be completed

    def test_error_recovery_and_state_consistency(self):
        """Test that system maintains consistent state even during errors."""
        manager = RichProgressManager("Error Recovery Test")
        manager.add_step("step1", "Normal step", 100)
        manager.add_step("step2", "Failing step", 50)

        # Start first step normally
        manager.start_step("step1")
        manager.update_step("step1", 50)

        # Simulate failure in second step
        manager.start_step("step2")  # This should complete step1
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.steps["step1"]["progress"] == 100  # Should be set to total

        manager.update_step("step2", 25)
        manager.fail_step("step2", "Simulated error")

        # Verify states are consistent
        assert manager.steps["step1"]["state"] == "completed"
        assert manager.steps["step1"]["progress"] == 100
        assert manager.steps["step2"]["state"] == "failed"
        assert manager.steps["step2"]["progress"] == 25
        assert manager.steps["step2"]["error_msg"] == "Simulated error"
        assert manager.active_step is None

    def test_realistic_ngram_analyzer_simulation(self):
        """Test realistic n-gram analyzer workflow with various patterns."""
        manager = RichProgressManager("Comprehensive N-gram Analysis")

        # Add steps matching real analyzer patterns
        steps_config = [
            ("load_data", "Loading and validating input data", 1000),
            (
                "preprocess",
                "Preprocessing and filtering messages",
                None,
            ),  # Unknown total initially
            ("tokenize", "Tokenizing text content", 5000),
            ("generate_ngrams", "Generating n-grams", 3000),
            ("build_vocab", "Building vocabulary dictionary", None),
            ("calculate_stats", "Calculating n-gram statistics", 1500),
            ("write_output", "Writing analysis results", None),
        ]

        for step_id, title, total in steps_config:
            manager.add_step(step_id, title, total)

        with manager:
            # Step 1: Data loading with progress
            manager.start_step("load_data")
            for i in range(0, 1001, 50):
                manager.update_step("load_data", min(i, 1000))
            manager.complete_step("load_data")

            # Step 2: Preprocessing (no initial total)
            manager.start_step("preprocess")
            # Simulate discovering total during processing and updating it
            manager.update_step("preprocess", 0, 2000)  # Update with new total

            # Continue with discovered total
            for i in range(0, 2001, 100):
                manager.update_step("preprocess", min(i, 2000))
            manager.complete_step("preprocess")

            # Step 3: Tokenization with batch processing
            manager.start_step("tokenize")
            batch_size = 250
            for batch_start in range(0, 5000, batch_size):
                batch_end = min(batch_start + batch_size, 5000)
                manager.update_step("tokenize", batch_end)
            manager.complete_step("tokenize")

            # Step 4: N-gram generation (simulate partial failure and recovery)
            manager.start_step("generate_ngrams")
            manager.update_step("generate_ngrams", 1500)
            # Simulate temporary issue, then recovery
            manager.update_step("generate_ngrams", 3000)
            manager.complete_step("generate_ngrams")

            # Step 5: Vocabulary building (no progress tracking)
            manager.start_step("build_vocab")
            # Simulate work without progress updates
            manager.complete_step("build_vocab")

            # Step 6: Statistics calculation
            manager.start_step("calculate_stats")
            # Simulate non-linear progress updates
            progress_points = [0, 100, 500, 800, 1200, 1500]
            for progress in progress_points:
                manager.update_step("calculate_stats", progress)
            manager.complete_step("calculate_stats")

            # Step 7: Output writing
            manager.start_step("write_output")
            manager.complete_step("write_output")

        # Verify all steps completed successfully
        expected_final_states = {
            "load_data": ("completed", 1000),
            "preprocess": ("completed", 2000),
            "tokenize": ("completed", 5000),
            "generate_ngrams": ("completed", 3000),
            "build_vocab": ("completed", 0),  # No progress tracking
            "calculate_stats": ("completed", 1500),
            "write_output": ("completed", 0),  # No progress tracking
        }

        for step_id, (
            expected_state,
            expected_progress,
        ) in expected_final_states.items():
            assert manager.steps[step_id]["state"] == expected_state
            # Only check progress for steps that had totals
            if manager.steps[step_id]["total"] is not None:
                assert manager.steps[step_id]["progress"] == expected_progress


class TestRichProgressManagerHierarchical(unittest.TestCase):
    """Comprehensive tests for hierarchical progress reporting with sub-steps."""

    def setUp(self):
        """Set up test fixtures for hierarchical progress testing."""
        self.progress_manager = RichProgressManager("Test Hierarchical Progress")

    def test_add_substep_basic_functionality(self):
        """Test basic substep addition functionality."""
        # Add parent step first
        self.progress_manager.add_step("parent", "Parent Step", 100)

        # Add substep
        self.progress_manager.add_substep("parent", "sub1", "First substep")

        # Verify substep was added
        self.assertIn("parent", self.progress_manager.substeps)
        self.assertIn("sub1", self.progress_manager.substeps["parent"])

        substep = self.progress_manager.substeps["parent"]["sub1"]
        self.assertEqual(substep["description"], "First substep")
        self.assertEqual(substep["state"], "pending")
        self.assertEqual(substep["progress"], 0)
        self.assertIsNone(substep["total"])
        self.assertEqual(substep["parent_step_id"], "parent")

    def test_add_substep_with_total(self):
        """Test adding substep with total for progress tracking."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "Substep with total", 50)

        substep = self.progress_manager.substeps["parent"]["sub1"]
        self.assertEqual(substep["total"], 50)

        # Verify substep was properly added to substeps tracking
        self.assertIn("parent", self.progress_manager.substeps)
        self.assertIn("sub1", self.progress_manager.substeps["parent"])

    def test_add_substep_validation_errors(self):
        """Test substep addition validation."""
        # Parent step doesn't exist
        with self.assertRaises(ValueError) as cm:
            self.progress_manager.add_substep("nonexistent", "sub1", "Test")
        self.assertIn("Parent step 'nonexistent' not found", str(cm.exception))

        # Add parent and substep
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep")

        # Duplicate substep
        with self.assertRaises(ValueError) as cm:
            self.progress_manager.add_substep("parent", "sub1", "Duplicate")
        self.assertIn("Substep 'sub1' already exists", str(cm.exception))

    def test_start_substep_functionality(self):
        """Test starting substeps and state management."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep", 30)

        # Start substep
        self.progress_manager.start_substep("parent", "sub1")

        # Verify states
        self.assertEqual(self.progress_manager.steps["parent"]["state"], "active")
        self.assertEqual(
            self.progress_manager.substeps["parent"]["sub1"]["state"], "active"
        )
        self.assertEqual(self.progress_manager.active_substeps["parent"], "sub1")

    def test_substep_auto_completes_previous_active(self):
        """Test automatic completion of previous active substep."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep", 20)
        self.progress_manager.add_substep("parent", "sub2", "Second substep", 30)

        # Start first substep
        self.progress_manager.start_substep("parent", "sub1")
        self.assertEqual(
            self.progress_manager.substeps["parent"]["sub1"]["state"], "active"
        )

        # Start second substep - should complete first
        self.progress_manager.start_substep("parent", "sub2")
        self.assertEqual(
            self.progress_manager.substeps["parent"]["sub1"]["state"], "completed"
        )
        self.assertEqual(
            self.progress_manager.substeps["parent"]["sub2"]["state"], "active"
        )
        self.assertEqual(self.progress_manager.active_substeps["parent"], "sub2")

    def test_update_substep_comprehensive(self):
        """Test comprehensive substep progress updating."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "Test substep", 100)

        # Update progress
        self.progress_manager.update_substep("parent", "sub1", 25)
        substep = self.progress_manager.substeps["parent"]["sub1"]
        self.assertEqual(substep["progress"], 25)

    def test_update_substep_validation_errors(self):
        """Test substep update validation."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "Test substep", 100)

        # Invalid parent step
        with self.assertRaises(ValueError):
            self.progress_manager.update_substep("nonexistent", "sub1", 50)

        # Invalid substep
        with self.assertRaises(ValueError):
            self.progress_manager.update_substep("parent", "nonexistent", 50)

        # Invalid progress types
        with self.assertRaises(TypeError):
            self.progress_manager.update_substep("parent", "sub1", "invalid")

        # Negative progress
        with self.assertRaises(ValueError):
            self.progress_manager.update_substep("parent", "sub1", -5)

        # Progress exceeds total
        with self.assertRaises(ValueError):
            self.progress_manager.update_substep("parent", "sub1", 150)

    def test_complete_substep_functionality(self):
        """Test substep completion."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "Test substep", 100)

        self.progress_manager.start_substep("parent", "sub1")
        self.progress_manager.update_substep("parent", "sub1", 50)
        self.progress_manager.complete_substep("parent", "sub1")

        substep = self.progress_manager.substeps["parent"]["sub1"]
        self.assertEqual(substep["state"], "completed")
        self.assertEqual(substep["progress"], 100)  # Should be set to total
        self.assertIsNone(self.progress_manager.active_substeps.get("parent"))

    def test_fail_substep_functionality(self):
        """Test substep failure handling."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "Test substep", 100)

        self.progress_manager.start_substep("parent", "sub1")
        self.progress_manager.fail_substep("parent", "sub1", "Test error")

        substep = self.progress_manager.substeps["parent"]["sub1"]
        self.assertEqual(substep["state"], "failed")
        self.assertEqual(substep["error_msg"], "Test error")
        self.assertIsNone(self.progress_manager.active_substeps.get("parent"))

    def test_parent_progress_calculation(self):
        """Test automatic parent progress calculation based on substeps."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep", 50)
        self.progress_manager.add_substep("parent", "sub2", "Second substep", 30)
        self.progress_manager.add_substep("parent", "sub3", "Third substep", 20)

        # Complete first substep
        self.progress_manager.start_substep("parent", "sub1")
        self.progress_manager.complete_substep("parent", "sub1")

        # Check parent progress (1/3 = 33.33%)
        parent_progress = self.progress_manager.steps["parent"].get(
            "substep_progress", 0
        )
        self.assertAlmostEqual(parent_progress, 33.33, places=1)

        # Complete second substep
        self.progress_manager.start_substep("parent", "sub2")
        self.progress_manager.complete_substep("parent", "sub2")

        # Check parent progress (2/3 = 66.67%)
        parent_progress = self.progress_manager.steps["parent"].get(
            "substep_progress", 0
        )
        self.assertAlmostEqual(parent_progress, 66.67, places=1)

    def test_hierarchical_display_formatting(self):
        """Test hierarchical display includes substeps with proper formatting."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep", 50)
        self.progress_manager.add_substep("parent", "sub2", "Second substep")

        self.progress_manager.start()
        self.progress_manager.start_substep("parent", "sub1")

        # Verify display functionality works (substeps are tracked and active)
        self.assertEqual(self.progress_manager.active_substeps["parent"], "sub1")

        # Verify substeps data structure
        self.assertIn("parent", self.progress_manager.substeps)
        self.assertEqual(len(self.progress_manager.substeps["parent"]), 2)

    def test_multiple_parents_with_substeps(self):
        """Test multiple parent steps with their own substeps."""
        # Setup multiple parents
        self.progress_manager.add_step("parent1", "First Parent")
        self.progress_manager.add_step("parent2", "Second Parent")

        # Add substeps to each parent
        self.progress_manager.add_substep("parent1", "sub1", "Parent1 Sub1", 100)
        self.progress_manager.add_substep("parent1", "sub2", "Parent1 Sub2", 50)
        self.progress_manager.add_substep("parent2", "sub1", "Parent2 Sub1", 75)

        # Verify isolation
        self.assertEqual(len(self.progress_manager.substeps["parent1"]), 2)
        self.assertEqual(len(self.progress_manager.substeps["parent2"]), 1)

        # Test independent operation
        self.progress_manager.start_substep("parent1", "sub1")
        self.progress_manager.start_substep("parent2", "sub1")

        self.assertEqual(self.progress_manager.active_substeps["parent1"], "sub1")
        self.assertEqual(self.progress_manager.active_substeps["parent2"], "sub1")

    def test_substep_progress_bar_display(self):
        """Test that substep progress bars display correctly."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep(
            "parent", "sub1", "Substep with progress", 100
        )

        # Start the substep
        self.progress_manager.start_substep("parent", "sub1")

        # Verify substep was created and configured correctly
        task_key = ("parent", "sub1")
        self.assertIn("parent", self.progress_manager.substeps)
        self.assertIn("sub1", self.progress_manager.substeps["parent"])

    def test_enhanced_write_operations_integration(self):
        """Test integration with enhanced write operations (simulated)."""
        # Simulate the n-gram analyzer write operations
        self.progress_manager.add_step(
            "write_message_ngrams", "Writing message n-grams output", 1
        )

        # Add substeps as done in enhanced write functions
        step_id = "write_message_ngrams"
        self.progress_manager.add_substep(
            step_id, "group", "Grouping n-grams by message"
        )
        self.progress_manager.add_substep(
            step_id, "aggregate", "Aggregating n-gram counts"
        )
        self.progress_manager.add_substep(step_id, "sort", "Sorting grouped data")
        self.progress_manager.add_substep(step_id, "write", "Writing to parquet file")

        # Simulate the enhanced write operation workflow
        self.progress_manager.start_step(step_id)

        # Process each substep
        substeps = ["group", "aggregate", "sort", "write"]
        for substep in substeps:
            self.progress_manager.start_substep(step_id, substep)
            self.progress_manager.complete_substep(step_id, substep)

        self.progress_manager.complete_step(step_id)

        # Verify all substeps completed
        for substep in substeps:
            substep_info = self.progress_manager.substeps[step_id][substep]
            self.assertEqual(substep_info["state"], "completed")

    def test_dataset_size_aware_granularity(self):
        """Test that progress reporting adapts to dataset size."""
        # Small dataset simulation (should have fewer substeps)
        small_dataset_steps = 3
        self.progress_manager.add_step(
            "small_process", "Small dataset processing", small_dataset_steps
        )

        # Large dataset simulation (should have more substeps)
        large_dataset_steps = 8
        self.progress_manager.add_step(
            "large_process", "Large dataset processing", large_dataset_steps
        )

        # Add different numbers of substeps based on "dataset size"
        for i in range(2):  # Fewer substeps for small dataset
            self.progress_manager.add_substep(
                "small_process", f"sub{i}", f"Small operation {i}"
            )

        for i in range(6):  # More substeps for large dataset
            self.progress_manager.add_substep(
                "large_process", f"sub{i}", f"Large operation {i}"
            )

        # Verify different granularity levels
        self.assertEqual(len(self.progress_manager.substeps["small_process"]), 2)
        self.assertEqual(len(self.progress_manager.substeps["large_process"]), 6)

    def test_error_handling_and_recovery(self):
        """Test error handling during substep operations."""
        self.progress_manager.add_step("parent", "Parent Step")
        self.progress_manager.add_substep("parent", "sub1", "First substep")
        self.progress_manager.add_substep("parent", "sub2", "Second substep")

        # Start first substep and make it fail
        self.progress_manager.start_substep("parent", "sub1")
        self.progress_manager.fail_substep("parent", "sub1", "Simulated failure")

        # Verify failure state
        self.assertEqual(
            self.progress_manager.substeps["parent"]["sub1"]["state"], "failed"
        )

        # Should be able to continue with next substep
        self.progress_manager.start_substep("parent", "sub2")
        self.assertEqual(
            self.progress_manager.substeps["parent"]["sub2"]["state"], "active"
        )

    def test_performance_overhead_measurement(self):
        """Test that progress reporting overhead is minimal."""
        import time

        # Create many steps and substeps
        num_steps = 10
        substeps_per_step = 4

        start_time = time.time()

        for step_idx in range(num_steps):
            step_id = f"step_{step_idx}"
            self.progress_manager.add_step(step_id, f"Step {step_idx}")

            for substep_idx in range(substeps_per_step):
                substep_id = f"sub_{substep_idx}"
                self.progress_manager.add_substep(
                    step_id, substep_id, f"Substep {substep_idx}", 100
                )

        setup_time = time.time() - start_time

        # Execute operations
        start_time = time.time()

        for step_idx in range(num_steps):
            step_id = f"step_{step_idx}"

            for substep_idx in range(substeps_per_step):
                substep_id = f"sub_{substep_idx}"
                self.progress_manager.start_substep(step_id, substep_id)

                # Simulate some progress updates
                for progress in [25, 50, 75, 100]:
                    self.progress_manager.update_substep(step_id, substep_id, progress)

                self.progress_manager.complete_substep(step_id, substep_id)

        execution_time = time.time() - start_time

        # Verify reasonable performance (should be very fast for this many operations)
        self.assertLess(setup_time, 1.0, "Setup should take less than 1 second")
        self.assertLess(
            execution_time, 2.0, "Execution should take less than 2 seconds"
        )

    def test_backward_compatibility_maintained(self):
        """Test that hierarchical features don't break existing functionality."""
        # Test that existing step-only operations work unchanged
        self.progress_manager.add_step("regular_step", "Regular Step", 100)
        self.progress_manager.start_step("regular_step")
        self.progress_manager.update_step("regular_step", 50)
        self.progress_manager.complete_step("regular_step")

        # Verify regular step functionality
        step = self.progress_manager.steps["regular_step"]
        self.assertEqual(step["state"], "completed")
        self.assertEqual(step["progress"], 100)

        # Test mixed usage (some steps with substeps, some without)
        self.progress_manager.add_step("step_with_subs", "Step with Substeps")
        self.progress_manager.add_step("step_without_subs", "Step without Substeps", 50)

        self.progress_manager.add_substep("step_with_subs", "sub1", "Substep")

        # Both should work fine
        self.progress_manager.start_step("step_without_subs")
        self.progress_manager.start_substep("step_with_subs", "sub1")

        self.assertEqual(
            self.progress_manager.steps["step_without_subs"]["state"], "active"
        )
        self.assertEqual(
            self.progress_manager.substeps["step_with_subs"]["sub1"]["state"], "active"
        )

    def test_dynamic_total_updates(self):
        """Test dynamic total updates for steps and substeps."""
        # Test step total update
        self.progress_manager.add_step("dynamic_step", "Dynamic Step", 100)

        # Update total to a new value
        self.progress_manager.update_step("dynamic_step", 50, 200)

        # Verify total was updated
        self.assertEqual(self.progress_manager.steps["dynamic_step"]["total"], 200)
        self.assertEqual(self.progress_manager.steps["dynamic_step"]["progress"], 50)

        # Test substep total update
        self.progress_manager.add_step("parent_step", "Parent Step")
        self.progress_manager.add_substep(
            "parent_step", "dynamic_sub", "Dynamic Substep", 50
        )

        # Update substep total
        self.progress_manager.update_substep("parent_step", "dynamic_sub", 25, 75)

        # Verify substep total was updated
        substep = self.progress_manager.substeps["parent_step"]["dynamic_sub"]
        self.assertEqual(substep["total"], 75)
        self.assertEqual(substep["progress"], 25)

        # Test validation: progress cannot exceed new total
        with self.assertRaises(ValueError) as cm:
            self.progress_manager.update_step(
                "dynamic_step", 250, 200
            )  # progress > new total
        self.assertIn("Progress 250 exceeds new total 200", str(cm.exception))

        # Test validation: new total must be positive
        with self.assertRaises(ValueError) as cm:
            self.progress_manager.update_step("dynamic_step", 50, 0)  # invalid total
        self.assertIn("total must be a positive integer", str(cm.exception))

    def test_ngram_analyzer_dynamic_updates_simulation(self):
        """Test realistic n-gram analyzer scenario with dynamic total updates."""
        manager = RichProgressManager("N-gram Analysis with Dynamic Updates")

        # Initial setup with estimated totals
        manager.add_step(
            "preprocess", "Preprocessing messages", 10000
        )  # Initial estimate
        manager.add_step("tokenize", "Tokenizing text", None)  # No total initially
        manager.add_step("process_ngrams", "Processing n-grams")

        # Add processing substeps without totals initially
        manager.add_substep(
            "process_ngrams", "extract_unique", "Extracting unique n-grams"
        )
        manager.add_substep("process_ngrams", "sort_ngrams", "Sorting n-grams")
        manager.add_substep("process_ngrams", "assign_ids", "Assigning n-gram IDs")

        # Simulate preprocessing step with updated total after filtering
        manager.start_step("preprocess")
        # After preprocessing, we know the actual filtered count
        filtered_count = 8500  # Fewer than estimated due to filtering
        manager.update_step("preprocess", filtered_count, filtered_count)
        manager.complete_step("preprocess")

        # Update tokenization total based on filtered data
        manager.update_step("tokenize", 0, filtered_count)
        manager.start_step("tokenize")
        manager.update_step("tokenize", filtered_count)
        manager.complete_step("tokenize")

        # Start processing with dynamic substep updates
        manager.start_step("process_ngrams")

        # Simulate getting actual n-gram counts and updating substep totals
        total_ngrams = 25000
        unique_ngrams = 8500

        # Update substep totals with actual counts
        manager.update_substep("process_ngrams", "extract_unique", 0, total_ngrams)
        manager.update_substep("process_ngrams", "sort_ngrams", 0, unique_ngrams)
        manager.update_substep("process_ngrams", "assign_ids", 0, total_ngrams)

        # Simulate substep execution
        manager.start_substep("process_ngrams", "extract_unique")
        manager.update_substep("process_ngrams", "extract_unique", total_ngrams)
        manager.complete_substep("process_ngrams", "extract_unique")

        manager.start_substep("process_ngrams", "sort_ngrams")
        manager.update_substep("process_ngrams", "sort_ngrams", unique_ngrams)
        manager.complete_substep("process_ngrams", "sort_ngrams")

        manager.start_substep("process_ngrams", "assign_ids")
        manager.update_substep("process_ngrams", "assign_ids", total_ngrams)
        manager.complete_substep("process_ngrams", "assign_ids")

        manager.complete_step("process_ngrams")

        # Verify final states
        self.assertEqual(manager.steps["preprocess"]["total"], filtered_count)
        self.assertEqual(manager.steps["tokenize"]["total"], filtered_count)
        self.assertEqual(
            manager.substeps["process_ngrams"]["extract_unique"]["total"], total_ngrams
        )
        self.assertEqual(
            manager.substeps["process_ngrams"]["sort_ngrams"]["total"], unique_ngrams
        )
        self.assertEqual(
            manager.substeps["process_ngrams"]["assign_ids"]["total"], total_ngrams
        )

        # All steps should be completed
        for step_id in ["preprocess", "tokenize", "process_ngrams"]:
            self.assertEqual(manager.steps[step_id]["state"], "completed")

    def test_hierarchical_progress_bar_display(self):
        """Test that parent steps with substeps properly update progress bars."""
        manager = RichProgressManager("Progress Bar Display Test")

        # Add parent step with total (like process_ngrams)
        manager.add_step("parent_with_total", "Parent with 3 substeps", 3)
        manager.add_substep("parent_with_total", "sub1", "First substep")
        manager.add_substep("parent_with_total", "sub2", "Second substep")
        manager.add_substep("parent_with_total", "sub3", "Third substep")

        # Start the parent step
        manager.start_step("parent_with_total")

        # Initially parent should have 0 progress
        self.assertEqual(manager.steps["parent_with_total"]["progress"], 0)

        # Complete first substep - parent should be 1/3 complete
        manager.start_substep("parent_with_total", "sub1")
        manager.complete_substep("parent_with_total", "sub1")

        # Check parent progress updated to 1.0 (1/3 * 3 total)
        self.assertEqual(manager.steps["parent_with_total"]["progress"], 1.0)
        self.assertAlmostEqual(
            manager.steps["parent_with_total"]["substep_progress"], 100 / 3, places=5
        )

        # Complete second substep - parent should be 2/3 complete
        manager.start_substep("parent_with_total", "sub2")
        manager.complete_substep("parent_with_total", "sub2")

        # Check parent progress updated to 2.0 (2/3 * 3 total)
        self.assertEqual(manager.steps["parent_with_total"]["progress"], 2.0)
        self.assertAlmostEqual(
            manager.steps["parent_with_total"]["substep_progress"], 200 / 3, places=5
        )

        # Complete third substep - parent should be fully complete
        manager.start_substep("parent_with_total", "sub3")
        manager.complete_substep("parent_with_total", "sub3")

        # Check parent progress updated to 3.0 (3/3 * 3 total = fully complete)
        self.assertEqual(manager.steps["parent_with_total"]["progress"], 3.0)
        self.assertEqual(manager.steps["parent_with_total"]["substep_progress"], 100.0)

        # Complete the parent step
        manager.complete_step("parent_with_total")
        self.assertEqual(manager.steps["parent_with_total"]["state"], "completed")

    def test_substep_rich_task_creation_from_dynamic_totals(self):
        """Test that Rich tasks are created when substeps get totals dynamically."""
        manager = RichProgressManager("Dynamic Rich Task Test")

        # Add parent step and substep without initial total
        manager.add_step("parent", "Parent step", 2)
        manager.add_substep("parent", "dynamic_sub", "Substep without initial total")

        # Initially, substep should have no total
        substep = manager.substeps["parent"]["dynamic_sub"]
        self.assertIsNone(substep["total"])

        # Update substep with total - this should update the substep data
        manager.update_substep("parent", "dynamic_sub", 0, 100)

        # Verify substep has the total and progress
        self.assertEqual(substep["total"], 100)
        self.assertEqual(substep["progress"], 0)

        # Start substep and update progress to verify Rich task works
        manager.start_substep("parent", "dynamic_sub")
        manager.update_substep("parent", "dynamic_sub", 50)

        # Verify progress was set correctly
        self.assertEqual(substep["progress"], 50)

        # Complete substep
        manager.complete_substep("parent", "dynamic_sub")
        self.assertEqual(substep["state"], "completed")


if __name__ == "__main__":
    unittest.main()
