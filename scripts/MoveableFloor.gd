extends StaticBody2D

func _ready():
	_set_tween()
	
func _set_tween():
	# 获取起止点节点（确保在编辑器中已设置）
	var start_point = $StartPoint
	var end_point = $EndPoint
	
	var start_pos: Vector2 = to_global(start_point.position)
	var end_pos: Vector2 = to_global(end_point.position)
	
	# 创建 Tween
	var tween: Tween = get_tree().create_tween()
	tween.tween_property(self, "position", end_pos, 2.0).set_trans(Tween.TRANS_LINEAR).set_ease(Tween.EASE_IN_OUT)
	
	# 可选：循环移动（从起点到终点，再回到起点）
	tween.tween_property(self, "position", start_pos, 2.0)
	tween.set_loops()  # 无限循环
