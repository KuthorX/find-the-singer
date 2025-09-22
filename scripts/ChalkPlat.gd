extends RigidBody2D

# Note: This script requires two Timer nodes as children: "FadeTimer" and "RespawnTimer".
# Connect the 'timeout' signal of both timers to the corresponding functions in this script.
# Connect the 'body_entered' signal of the RigidBody2D to the '_on_body_entered' function.

@onready var collision_shape = $CollisionShape2D
@onready var fade_timer = $FadeTimer
@onready var respawn_timer = $RespawnTimer

func _on_body_entered(body):
	if body.is_in_group("player"):
		fade_timer.start()

func _on_fade_timer_timeout():
	# Disappear
	collision_shape.disabled = true
	visible = false
	respawn_timer.start()

func _on_respawn_timer_timeout():
	# Reappear
	collision_shape.disabled = false
	visible = true
