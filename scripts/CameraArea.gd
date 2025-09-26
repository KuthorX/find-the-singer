extends Area2D

signal mode_changed(new_mode: CameraModes.CameraMode, step_x: float, step_y: float)
@export var camera_mode: CameraModes.CameraMode
@export var step_threshold_x: float = 200.0  # Step size for x-axis in STEPPED mode
@export var step_threshold_y: float = 500.0  # Step size for y-axis in STEPPED mode

func _ready():
	connect("body_entered", _on_body_entered)
	connect("body_exited", _on_body_exited)

func _on_body_entered(body):
	if body.is_in_group("player"):  # Changed to group for consistency
		print("Emitting mode_changed: ", camera_mode, " ", step_threshold_x, " ", step_threshold_y)
		emit_signal("mode_changed", camera_mode, step_threshold_x, step_threshold_y)

func _on_body_exited(body):
	if body.is_in_group("player"):
		# Revert to FULL_FOLLOW with default thresholds
		emit_signal("mode_changed", CameraModes.CameraMode.FULL_FOLLOW, 200.0, 200.0)
