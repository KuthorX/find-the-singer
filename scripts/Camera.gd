extends Camera2D

@export var target: Node2D
@export var map_min_x: float = 0.0
@export var map_max_x: float = 1920.0
@export var map_min_y: float = 0.0
@export var map_max_y: float = 1080.0
@export var smooth_speed: float = 5.0
@export var default_step_threshold_x: float = 200.0  # Default for non-STEPPED or fallback
@export var default_step_threshold_y: float = 200.0
var current_mode: CameraModes.CameraMode = CameraModes.CameraMode.FULL_FOLLOW
var fixed_position: Vector2 = Vector2.ZERO
var target_step_x: float = 0.0
var target_step_y: float = 0.0
var current_step_threshold_x: float = 200.0
var current_step_threshold_y: float = 200.0

func _ready():
	make_current()
	if target:
		global_position = target.global_position
		fixed_position = global_position
		target_step_x = global_position.x
		target_step_y = global_position.y
		current_step_threshold_x = default_step_threshold_x
		current_step_threshold_y = default_step_threshold_y
	var areas = get_tree().get_nodes_in_group("camera_areas")
	for area in areas:
		area.mode_changed.connect(_on_mode_changed)

func _on_mode_changed(new_mode: CameraModes.CameraMode, step_x: float, step_y: float):
	set_mode_and_thresholds(new_mode, step_x, step_y)

func set_mode_and_thresholds(new_mode: CameraModes.CameraMode, step_x: float, step_y: float):
	current_mode = new_mode
	if current_mode == CameraModes.CameraMode.FIXED:
		fixed_position = global_position
	if current_mode == CameraModes.CameraMode.STEPPED:
		current_step_threshold_x = max(step_x, 1.0)  # Avoid division by zero
		current_step_threshold_y = max(step_y, 1.0)
		# Snap to nearest step to avoid jumps
		if target:
			var player_step_x = floor(target.global_position.x / current_step_threshold_x)
			var player_step_y = floor(target.global_position.y / current_step_threshold_y)
			target_step_x = player_step_x * current_step_threshold_x
			target_step_y = player_step_y * current_step_threshold_y
	else:
		current_step_threshold_x = default_step_threshold_x
		current_step_threshold_y = default_step_threshold_y

func _process(delta):
	if target:
		var target_position = target.global_position
		var viewport_size = get_viewport_rect().size / zoom
		var camera_extents = viewport_size / 2.0

		var new_position = global_position

		match current_mode:
			CameraModes.CameraMode.FULL_FOLLOW:
				new_position = target_position
			CameraModes.CameraMode.X_ONLY:
				new_position.x = target_position.x
			CameraModes.CameraMode.Y_ONLY:
				new_position.y = target_position.y
			CameraModes.CameraMode.FIXED:
				new_position = fixed_position
			CameraModes.CameraMode.STEPPED:
				var player_step_x = floor(target_position.x / current_step_threshold_x)
				if player_step_x != floor(target_step_x / current_step_threshold_x):
					target_step_x = player_step_x * current_step_threshold_x
				new_position.x = target_step_x
				var player_step_y = floor(target_position.y / current_step_threshold_y)
				if player_step_y != floor(target_step_y / current_step_threshold_y):
					target_step_y = player_step_y * current_step_threshold_y
				new_position.y = target_step_y

		new_position.x = clamp(new_position.x, map_min_x + camera_extents.x, map_max_x - camera_extents.x)
		new_position.y = clamp(new_position.y, map_min_y + camera_extents.y, map_max_y - camera_extents.y)

		global_position = global_position.lerp(new_position, smooth_speed * delta)
