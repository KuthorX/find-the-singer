extends CharacterBody2D

@export var SPEED = 300.0
@export var ACCEL_SPEED = 600.0
@export var JUMP_VELOCITY = -400.0

# Each platform's notation has its own landing voice (see docs/audio-direction.md).
const PLATFORM_SOUNDS := {
	"plat_spring": "bounce",
	"plat_fragile": "land_fragile",
	"plat_repeat": "land_repeat",
	"plat_gliss": "land_gliss",
}
const DEFAULT_LAND_SOUND := "land_measure"
const LAND_MIN_AIR_SECONDS := 0.12
const LAND_MIN_FALL_SPEED := 260.0  # tiny skitter hops (e.g. on the glissando) stay silent
const LAND_SOFT_DB := -9.0
const LAND_HARD_FALL_SPEED := 900.0
const LAND_REPEAT_MS := 300  # sliding/bouncing contacts must not machine-gun the landing voice

var has_jump_before_on_floor = false
var _air_seconds := 0.0
var _last_land_ms := -LAND_REPEAT_MS
var checkpoint_pos = Vector2.ZERO
var init_checkpoint_pos = Vector2.ZERO

# Get the gravity from the project settings to be synced with RigidBody nodes.
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

func _ready() -> void:
	checkpoint_pos = position
	init_checkpoint_pos = checkpoint_pos

func is_player():
	pass

func _physics_process(delta):
	# Add the gravity.
	if not is_on_floor():
		velocity.y += gravity * delta
	
	if is_on_floor():
		has_jump_before_on_floor = false

	# Handle jump.
	if Input.is_action_just_pressed("ui_accept") and not has_jump_before_on_floor:
		velocity.y = JUMP_VELOCITY
		has_jump_before_on_floor = true
		AudioManager.play_sfx("jump")

	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	var direction = Input.get_axis("ui_left", "ui_right")
	var current_speed = SPEED
	if Input.is_action_pressed("ui_shift"):
		current_speed = ACCEL_SPEED
	
	if direction:
		velocity.x = direction * current_speed
		$Sprite2D.scale.x = signf(direction)  # face the walking direction
	else:
		velocity.x = 0

	var was_on_floor := is_on_floor()
	var fall_speed := velocity.y
	move_and_slide()
	if is_on_floor():
		if not was_on_floor and _air_seconds >= LAND_MIN_AIR_SECONDS and fall_speed >= LAND_MIN_FALL_SPEED:
			_play_landing(fall_speed)
		_air_seconds = 0.0
	else:
		_air_seconds += delta

func _play_landing(fall_speed: float) -> void:
	var now := Time.get_ticks_msec()
	if now - _last_land_ms < LAND_REPEAT_MS:
		return
	_last_land_ms = now
	var volume_db := lerpf(LAND_SOFT_DB, 0.0, clampf(fall_speed / LAND_HARD_FALL_SPEED, 0.0, 1.0))
	AudioManager.play_sfx(_landing_sound(), volume_db)

func _landing_sound() -> String:
	for i in get_slide_collision_count():
		var collision := get_slide_collision(i)
		if collision.get_normal().dot(up_direction) < 0.7:
			continue
		var collider := collision.get_collider() as Node
		if collider == null:
			continue
		# Fragile measures keep their sprite on the parent of the colliding body.
		for node: Node in [collider, collider.get_parent()]:
			var sprite := node.get_node_or_null("Sprite2D") as Sprite2D
			if sprite and sprite.texture:
				var file := sprite.texture.resource_path.get_file().get_basename()
				return PLATFORM_SOUNDS.get(file, DEFAULT_LAND_SOUND)
	return DEFAULT_LAND_SOUND

func move_to_checkpoint():
	velocity = Vector2.ZERO
	position = checkpoint_pos

func save_checkpoint(checkpoint_position: Vector2):
	checkpoint_pos = checkpoint_position

func reset_to_init_checkpoint():
	checkpoint_pos = init_checkpoint_pos
	move_to_checkpoint()
