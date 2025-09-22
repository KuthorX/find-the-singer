extends RigidBody2D

# 注意：需要将此节点添加到"letter_bonus"组中
# 需要将body_entered信号连接到_on_body_entered函数

func _ready():
	# 确保物理处理正常工作
	contact_monitor = true
	max_contacts_reported = 4

func _on_body_entered(body):
	if body.is_in_group("player"):
		# 更新GameState中的计数器
		var game_state = get_node("/root/GameState")
		game_state.collect_letter_bonus()
		
		# 信件消失
		queue_free()
