extends RigidBody2D

# Note: Connect the 'body_entered' signal of the RigidBody2D to the '_on_body_entered' function in the Godot editor.
@export var bounce_power = -600.0

func _on_body_entered(body):
	if body.is_in_group("player"):
		body.velocity.y = bounce_power
