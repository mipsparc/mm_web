from svg.charts.plot import Plot

class Chart:
    # 加速曲線のSVGデータを作成する
    @classmethod
    def createSpeedAccel(self, profiles):
        g = Plot(
                dict(
                    width=700,
                    height=640,
                    graph_title="加速曲線",
                    show_graph_title=True,
                    no_css=True,
                    key=True,
                    scale_x_integers=True,
                    min_x_value=0,
                    min_y_value=0,
                    show_data_labels=True,
                    show_x_guidelines=True,
                    show_x_title=True,
                    x_title="速度",
                    show_y_title=True,
                    y_title="加速度",
                    y_title_text_direction='bt',
                    scale_y_divisions=0.05
                )
            )
        
        g.scale_x_divisions=10
        
        for profile in profiles:
            g.add_data({
                'data': profile[1],
                'title': f'{profile[0]}'
            })
        
        return g.burn()
    
    # 出力曲線のSVGデータを作成する
    @classmethod
    def createSpeedOutput(self, profiles):
        g = Plot(
                dict(
                    width=700,
                    height=640,
                    graph_title="出力曲線",
                    show_graph_title=True,
                    no_css=True,
                    key=True,
                    scale_x_integers=True,
                    scale_y_integers=True,
                    min_x_value=0,
                    min_y_value=0,
                    show_data_labels=True,
                    show_x_guidelines=True,
                    show_x_title=True,
                    x_title="速度",
                    show_y_title=True,
                    y_title="出力値",
                    y_title_text_direction='bt',
                )
            )
        
        g.scale_x_divisions=10
        
        for profile in profiles:
            g.add_data({
                'data': profile[1],
                'title': f'{profile[0]}'
            })
        
        return g.burn()

    @classmethod
    def genAccelProfileFromCurveGroups(self, curve_groups):
        profiles = []
        for curve_group_id, curves in curve_groups.items():
            profile = []
            for curve in curves:
                profile.append(curve['speed'])
                profile.append(curve['accel'])
            profiles.append([curve_group_id, profile])
            
        return profiles
    
    
    @classmethod
    def genOutputProfileFromCurveGroups(self, curve_groups):
        profiles = []
        for curve_group_id, curves in curve_groups.items():
            profile = []
            for curve in curves:
                profile.append(curve['speed'])
                profile.append(curve['output'])
            profiles.append([curve_group_id, profile])
            
        return profiles
