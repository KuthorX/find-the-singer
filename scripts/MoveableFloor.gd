extends AnimatableBody2D

@export var moveToEndSeconds = 2.0
@export var moveToStartSeconds = 2.0

func _ready():
	# Get start and end points (ensure set in editor as child nodes like Marker2D)
	var start_point = $StartPoint
	var end_point = $EndPoint
	var start_pos: Vector2 = to_global(start_point.position)
	var end_pos: Vector2 = to_global(end_point.position)
	
	# Set initial position to start
	global_position = start_pos
	
	# Create Tween with physics processing to sync with physics step (prevents jitter)
	var tween: Tween = get_tree().create_tween()
	tween.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)  # Key fix for synchronization
	tween.tween_property(self, "global_position", end_pos, moveToEndSeconds).set_trans(Tween.TRANS_LINEAR).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "global_position", start_pos, moveToStartSeconds).set_trans(Tween.TRANS_LINEAR).set_ease(Tween.EASE_IN_OUT)
	tween.set_loops()  # Infinite loop
