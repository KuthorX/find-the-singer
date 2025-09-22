extends CharacterBody2D

@export var SPEED = 300.0
@export var ACCEL_SPEED = 600.0
@export var JUMP_VELOCITY = -400.0

# Get the gravity from the project settings to be synced with RigidBody nodes.
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

func _physics_process(delta):
	# Add the gravity.
	if not is_on_floor():
		print("not is_on_floor")
		velocity.y += gravity * delta

	# Handle jump.
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		print("is_on_floor and jump")
		velocity.y = JUMP_VELOCITY

	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	var direction = Input.get_axis("ui_left", "ui_right")
	var current_speed = SPEED
	if Input.is_action_pressed("ui_shift"):
		current_speed = ACCEL_SPEED
	
	if direction:
		print("direction hit")
		velocity.x = direction * current_speed
	else:
		velocity.x = 0

	move_and_slide()
	
	for i in range(get_slide_collision_count()):
		var collision = get_slide_collision(i)
		if "Groud" in collision.get_collider().name:
			print("碰撞已发生")
