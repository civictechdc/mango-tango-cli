"""
Tests for ProgressManager memory monitoring functionality.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.utils import MemoryManager, MemoryPressureLevel
from terminal_tools.progress import ProgressManager


class TestProgressManagerMemoryFeatures:
    """Test ProgressManager memory monitoring functionality."""

    def test_initialization_with_memory_manager(self):
        """Test ProgressManager initializes correctly with memory manager."""
        memory_manager = MagicMock(spec=MemoryManager)
        progress_manager = ProgressManager(
            "Test Analysis", memory_manager=memory_manager
        )

        assert progress_manager.memory_manager == memory_manager
        assert progress_manager.last_memory_warning == 0
        assert "Test Analysis" in progress_manager.title

    def test_initialization_without_memory_manager(self):
        """Test ProgressManager initializes correctly without memory manager."""
        progress_manager = ProgressManager("Test Analysis")

        assert progress_manager.memory_manager is None
        assert progress_manager.last_memory_warning is None
        assert "Test Analysis" in progress_manager.title

    def test_update_step_with_memory_low_pressure(self):
        """Test memory-aware step updates with low memory pressure."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {
            "rss_mb": 500.0,
            "process_memory_percent": 12.5,
            "pressure_level": "low",
        }
        memory_manager.should_trigger_gc.return_value = False

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)
        progress_manager.add_step("test_step", "Testing", 100)

        # Should update normally without warnings
        progress_manager.update_step_with_memory("test_step", 50, "testing")

        # Verify memory stats were retrieved
        memory_manager.get_current_memory_usage.assert_called_once()
        memory_manager.should_trigger_gc.assert_called_once()

        memory_manager.enhanced_gc_cleanup.assert_not_called()

    def test_update_step_with_memory_high_pressure(self):
        """Test memory-aware step updates with high memory pressure."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {
            "rss_mb": 3000.0,
            "process_memory_percent": 75.0,
            "pressure_level": "high",
        }
        memory_manager.should_trigger_gc.return_value = True
        memory_manager.enhanced_gc_cleanup.return_value = {"memory_freed_mb": 100.0}

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)
        progress_manager.add_step("test_step", "Testing", 100)

        with patch("rich.console.Console.print"):
            progress_manager.update_step_with_memory(
                "test_step", 75, "high pressure test"
            )

        memory_manager.enhanced_gc_cleanup.assert_called_once()

    def test_update_step_with_memory_critical_pressure(self):
        """Test memory-aware step updates with critical memory pressure."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {
            "rss_mb": 3500.0,
            "process_memory_percent": 87.5,
            "pressure_level": "critical",
        }
        memory_manager.should_trigger_gc.return_value = True
        memory_manager.enhanced_gc_cleanup.return_value = {"memory_freed_mb": 200.0}

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)
        progress_manager.add_step("test_step", "Testing", 100)

        with patch.object(progress_manager, "_display_memory_warning") as mock_warning:
            progress_manager.update_step_with_memory("test_step", 90, "critical test")
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert call_args[0] == MemoryPressureLevel.CRITICAL

    def test_memory_warning_throttling(self):
        """Test that memory warnings are throttled to avoid spam."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {
            "rss_mb": 3000.0,
            "process_memory_percent": 75.0,
            "pressure_level": "high",
        }

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)
        progress_manager.add_step("test_step", "Testing", 100)

        with patch("rich.console.Console.print") as mock_console_print:
            progress_manager._display_memory_warning(
                MemoryPressureLevel.HIGH,
                {"rss_mb": 3000.0, "process_memory_percent": 75.0},
                "test context",
            )
            first_call_count = mock_console_print.call_count

            progress_manager._display_memory_warning(
                MemoryPressureLevel.HIGH,
                {"rss_mb": 3000.0, "process_memory_percent": 75.0},
                "test context",
            )
            second_call_count = mock_console_print.call_count

            assert second_call_count == first_call_count

    def test_memory_warning_throttling_timeout(self):
        """Test that memory warnings can be displayed again after timeout."""
        memory_manager = MagicMock(spec=MemoryManager)
        progress_manager = ProgressManager("Test", memory_manager=memory_manager)

        progress_manager.last_memory_warning = time.time() - 31

        with patch("rich.console.Console.print") as mock_console_print:
            progress_manager._display_memory_warning(
                MemoryPressureLevel.HIGH,
                {"rss_mb": 3000.0, "process_memory_percent": 75.0},
                "test context",
            )

            mock_console_print.assert_called()

    def test_display_memory_warning_content(self):
        """Test the content and formatting of memory warnings."""
        memory_manager = MagicMock(spec=MemoryManager)
        progress_manager = ProgressManager("Test", memory_manager=memory_manager)

        with patch("rich.console.Console.print") as mock_console_print:
            # Test HIGH pressure warning
            progress_manager._display_memory_warning(
                MemoryPressureLevel.HIGH,
                {"rss_mb": 3000.0, "process_memory_percent": 75.0},
                "n-gram generation",
            )

            mock_console_print.assert_called()
            call_args = mock_console_print.call_args
            assert call_args is not None, "mock_console.print was not called with arguments"
            call_args = call_args[0]
            panel = call_args[0]

            assert panel.border_style == "yellow"
            assert "Current usage: 3000.0MB" in str(panel.renderable)
            assert "n-gram generation" in str(panel.renderable)
            assert "Memory Pressure: HIGH" in str(panel.renderable)

            mock_console_print.reset_mock()
            progress_manager.last_memory_warning = None
            progress_manager._display_memory_warning(
                MemoryPressureLevel.CRITICAL,
                {"rss_mb": 3500.0, "process_memory_percent": 87.5},
                "unique extraction",
            )

            call_args = mock_console_print.call_args
            assert call_args is not None, "mock_console.print was not called with arguments"
            call_args = call_args[0]
            panel = call_args[0]

            assert panel.border_style == "red"
            assert "Memory Pressure: CRITICAL" in str(panel.renderable)
            assert "unique extraction" in str(panel.renderable)

    def test_display_memory_summary(self):
        """Test memory summary display."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {
            "rss_mb": 2500.0,
            "peak_rss_mb": 3000.0,
            "available_mb": 1500.0,
            "pressure_level": "medium",
        }

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)

        with patch("rich.console.Console.print") as mock_console_print:
            progress_manager.display_memory_summary()

            mock_console_print.assert_called()
            call_args = mock_console_print.call_args
            assert call_args is not None, "mock_console.print was not called with arguments"
            call_args = call_args[0]
            panel = call_args[0]

            assert panel.border_style == "green"
            assert "Peak memory usage: 3000.0MB" in str(panel.renderable)
            assert "Final memory usage: 2500.0MB" in str(panel.renderable)
            assert "Available memory: 1500.0MB" in str(panel.renderable)
            assert "Final pressure level: medium" in str(panel.renderable)

    def test_garbage_collection_reporting(self):
        """Test garbage collection effectiveness reporting."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {"pressure_level": "low"}
        memory_manager.should_trigger_gc.return_value = True
        memory_manager.enhanced_gc_cleanup.return_value = {
            "memory_freed_mb": 150.0  # Significant cleanup
        }

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)
        progress_manager.add_step("test_step", "Testing", 100)

        with patch("rich.console.Console.print") as mock_console_print:
            progress_manager.update_step_with_memory("test_step", 50, "gc test")

            print_calls = [str(call) for call in mock_console_print.call_args_list]
            assert any("Freed 150.0MB memory" in call for call in print_calls)

    def test_no_gc_reporting_for_small_cleanup(self):
        """Test that small GC cleanups are not reported to avoid noise."""
        memory_manager = MagicMock(spec=MemoryManager)
        memory_manager.get_current_memory_usage.return_value = {"pressure_level": "low"}
        memory_manager.should_trigger_gc.return_value = True
        memory_manager.enhanced_gc_cleanup.return_value = {
            "memory_freed_mb": 10.0  # Small cleanup
        }

        progress_manager = ProgressManager("Test", memory_manager=memory_manager)
        progress_manager.add_step("test_step", "Testing", 100)

        with patch("rich.console.Console.print") as mock_console_print:
            progress_manager.update_step_with_memory("test_step", 50, "small gc test")

            print_calls = [str(call) for call in mock_console_print.call_args_list]
            assert not any(
                "Freed" in call and "MB memory" in call for call in print_calls
            )


class TestProgressManagerMemoryIntegration:
    """Integration tests for ProgressManager memory features."""

    def test_full_analysis_simulation(self):
        """Simulate a full analysis workflow with memory monitoring."""
        memory_manager = MagicMock(spec=MemoryManager)

        # Simulate increasing memory pressure during analysis
        memory_states = [
            {"rss_mb": 500.0, "process_memory_percent": 12.5, "pressure_level": "low"},
            {"rss_mb": 1500.0, "process_memory_percent": 37.5, "pressure_level": "low"},
            {
                "rss_mb": 2500.0,
                "process_memory_percent": 62.5,
                "pressure_level": "medium",
            },
            {
                "rss_mb": 3200.0,
                "process_memory_percent": 80.0,
                "pressure_level": "high",
            },
            {
                "rss_mb": 2800.0,
                "process_memory_percent": 70.0,
                "pressure_level": "medium",
            },  # After cleanup
        ]

        memory_manager.get_current_memory_usage.side_effect = memory_states + [
            {
                "rss_mb": 2800.0,
                "process_memory_percent": 70.0,
                "pressure_level": "medium",
            }
        ]
        memory_manager.should_trigger_gc.side_effect = [
            False,
            False,
            False,
            True,
            False,
        ]
        memory_manager.enhanced_gc_cleanup.return_value = {"memory_freed_mb": 400.0}

        progress_manager = ProgressManager(
            "Simulated Analysis", memory_manager=memory_manager
        )

        steps = ["preprocess", "tokenize", "ngrams", "extract_unique", "write_output"]
        for step in steps:
            progress_manager.add_step(step, f"Processing {step}", 100)

        with patch("rich.console.Console.print"):
            for i, step in enumerate(steps):
                progress_manager.start_step(step)
                progress_manager.update_step_with_memory(step, 50, f"{step} processing")
                progress_manager.complete_step(step)

            progress_manager.display_memory_summary()

        assert memory_manager.get_current_memory_usage.call_count == len(steps) + 1
        assert memory_manager.should_trigger_gc.call_count == len(steps)
        assert memory_manager.enhanced_gc_cleanup.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
