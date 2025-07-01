#!/usr/bin/env python3
"""
Модуль для создания интерактивных графиков с помощью Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import os

class InteractivePlotGenerator:
    """Генератор интерактивных графиков"""
    
    def __init__(self, df, output_dir, special_columns=None):
        self.df = df
        self.output_dir = output_dir
        self.plots = {}
        self.special_columns = special_columns or []
        
        # Исключаем специальные столбцы из числовых для статистических вычислений
        self.numerical_cols = [col for col in self.df.select_dtypes(include=[np.number]).columns 
                              if col not in self.special_columns]
        print(f"Числовые столбцы для интерактивных графиков (исключая специальные): {self.numerical_cols}")
        print(f"Специальные столбцы (исключены из интерактивных графиков): {self.special_columns}")
        
    def create_interactive_plots(self):
        """Создание всех интерактивных графиков"""
        print("Создание интерактивных графиков...")
        
        # Определяем типы данных
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        date_cols = [col for col in self.df.columns if pd.api.types.is_datetime64_any_dtype(self.df[col])]
        
        # 1. Распределения числовых переменных (исключая специальные)
        for col in self.numerical_cols:
            self.create_distribution_plot(col)
        
        # 2. Корреляционная матрица (исключая специальные)
        if len(self.numerical_cols) > 1:
            self.create_correlation_heatmap(self.numerical_cols)
        
        # 3. Scatter plots для пар числовых переменных (исключая специальные)
        if len(self.numerical_cols) >= 2:
            self.create_scatter_plots(self.numerical_cols)
        
        # 4. Категориальные переменные
        for col in categorical_cols:
            if self.df[col].nunique() < 20:
                self.create_categorical_plot(col)
        
        # 5. Временные ряды (исключая специальные)
        for date_col in date_cols:
            if len(self.numerical_cols) > 0:
                for num_col in self.numerical_cols[:3]:  # Ограничиваем первыми 3
                    self.create_time_series_plot(date_col, num_col)
        
        # 6. Box plots для выбросов (исключая специальные)
        for col in self.numerical_cols:
            self.create_box_plot(col)
        
        # 7. Продвинутые интерактивные графики (исключая специальные)
        if len(self.numerical_cols) >= 2:
            print('Создаю parallel coordinates plot...')
            self.create_parallel_coordinates_plot(self.numerical_cols)
        
        if len(self.numerical_cols) >= 3:
            print('Создаю 3D scatter plot...')
            self.create_3d_scatter_plot(self.numerical_cols)
            print('Создаю scatter matrix...')
            self.create_scatter_matrix(self.numerical_cols)
        
        # 8. Статистические графики (исключая специальные)
        for col in self.numerical_cols:
            print(f'Создаю Q-Q plot для {col}...')
            self.create_qq_plot(col)
        
        # Сохраняем все графики в JSON
        self.save_plots_json()
        
        return self.plots
    
    def create_distribution_plot(self, column):
        """Создание интерактивного графика распределения"""
        fig = go.Figure()
        
        # Гистограмма
        fig.add_trace(go.Histogram(
            x=self.df[column].dropna(),
            nbinsx=30,
            name='Гистограмма',
            opacity=0.7,
            marker_color='skyblue'
        ))
        
        # Кривая плотности (упрощенная версия)
        try:
            from scipy import stats
            data = self.df[column].dropna()
            kde_x = np.linspace(data.min(), data.max(), 100)
            kde = stats.gaussian_kde(data)
            kde_y = kde(kde_x) * len(data) * (data.max() - data.min()) / 30
            
            fig.add_trace(go.Scatter(
                x=kde_x,
                y=kde_y,
                mode='lines',
                name='Плотность',
                line=dict(color='red', width=2)
            ))
        except ImportError:
            # Если scipy недоступен, пропускаем кривую плотности
            pass
        
        fig.update_layout(
            title=f'Распределение: {column}',
            xaxis_title=column,
            yaxis_title='Частота',
            hovermode='x unified',
            showlegend=True,
            template='plotly_white'
        )
        
        # Сохраняем как HTML
        filename = f'interactive_dist_{column}.html'
        filepath = os.path.join(self.output_dir, filename)
        fig.write_html(filepath)
        
        self.plots[f'distribution_{column}'] = {
            'type': 'distribution',
            'column': column,
            'path': filename,
            'plot_data': fig.to_json()
        }
    
    def create_correlation_heatmap(self, numerical_cols):
        """Создание интерактивной корреляционной матрицы"""
        corr_matrix = self.df[numerical_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='Корреляционная матрица',
            xaxis_title='Переменные',
            yaxis_title='Переменные',
            template='plotly_white'
        )
        
        filename = 'interactive_correlation.html'
        filepath = os.path.join(self.output_dir, filename)
        fig.write_html(filepath)
        
        self.plots['correlation'] = {
            'type': 'correlation',
            'path': filename,
            'plot_data': fig.to_json()
        }
    
    def create_scatter_plots(self, numerical_cols):
        """Создание интерактивных scatter plots"""
        # Ограничиваем количество пар
        max_pairs = min(6, (len(numerical_cols) * (len(numerical_cols) - 1)) // 2)
        pairs_count = 0
        
        for i, col1 in enumerate(numerical_cols):
            for col2 in numerical_cols[i+1:]:
                if pairs_count >= max_pairs:
                    break
                
                fig = go.Figure()
                
                # Scatter plot
                fig.add_trace(go.Scatter(
                    x=self.df[col1],
                    y=self.df[col2],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=self.df[col1],  # Цвет по первой переменной
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title=col1)
                    ),
                    text=f'{col1}: %{{x}}<br>{col2}: %{{y}}',
                    hovertemplate='<b>%{text}</b><extra></extra>'
                ))
                
                # Линия тренда
                if abs(self.df[col1].corr(self.df[col2])) > 0.3:
                    z = np.polyfit(self.df[col1].dropna(), self.df[col2].dropna(), 1)
                    p = np.poly1d(z)
                    fig.add_trace(go.Scatter(
                        x=self.df[col1],
                        y=p(self.df[col1]),
                        mode='lines',
                        name='Тренд',
                        line=dict(color='red', dash='dash')
                    ))
                
                fig.update_layout(
                    title=f'{col1} vs {col2}',
                    xaxis_title=col1,
                    yaxis_title=col2,
                    template='plotly_white'
                )
                
                filename = f'interactive_scatter_{col1}_{col2}.html'
                filepath = os.path.join(self.output_dir, filename)
                fig.write_html(filepath)
                
                self.plots[f'scatter_{col1}_{col2}'] = {
                    'type': 'scatter',
                    'x_column': col1,
                    'y_column': col2,
                    'path': filename,
                    'plot_data': fig.to_json()
                }
                
                pairs_count += 1
    
    def create_categorical_plot(self, column):
        """Создание интерактивного графика для категориальных данных"""
        value_counts = self.df[column].value_counts().head(10)
        
        fig = go.Figure(data=[
            go.Bar(
                x=value_counts.index,
                y=value_counts.values,
                marker_color='lightcoral',
                text=value_counts.values,
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title=f'Топ-10 категорий: {column}',
            xaxis_title=column,
            yaxis_title='Количество',
            template='plotly_white'
        )
        
        filename = f'interactive_bar_{column}.html'
        filepath = os.path.join(self.output_dir, filename)
        fig.write_html(filepath)
        
        self.plots[f'bar_{column}'] = {
            'type': 'bar',
            'column': column,
            'path': filename,
            'plot_data': fig.to_json()
        }
    
    def create_time_series_plot(self, date_col, value_col):
        """Создание интерактивного временного ряда"""
        time_series = self.df.groupby(date_col)[value_col].mean().sort_index()
        
        fig = go.Figure()
        
        # Основной временной ряд
        fig.add_trace(go.Scatter(
            x=time_series.index,
            y=time_series.values,
            mode='lines+markers',
            name=value_col,
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        # Скользящее среднее
        if len(time_series) > 7:
            window_size = min(7, len(time_series) // 4)
            rolling_mean = time_series.rolling(window=window_size).mean()
            fig.add_trace(go.Scatter(
                x=rolling_mean.index,
                y=rolling_mean.values,
                mode='lines',
                name=f'Скользящее среднее (окно={window_size})',
                line=dict(color='red', dash='dash')
            ))
        
        fig.update_layout(
            title=f'Временной ряд: {value_col} по {date_col}',
            xaxis_title=date_col,
            yaxis_title=value_col,
            template='plotly_white',
            hovermode='x unified'
        )
        
        filename = f'interactive_timeseries_{date_col}_{value_col}.html'
        filepath = os.path.join(self.output_dir, filename)
        fig.write_html(filepath)
        
        self.plots[f'timeseries_{date_col}_{value_col}'] = {
            'type': 'time_series',
            'x_column': date_col,
            'y_column': value_col,
            'path': filename,
            'plot_data': fig.to_json()
        }
    
    def create_box_plot(self, column):
        """Создание интерактивного box plot для анализа выбросов"""
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=self.df[column].dropna(),
            name=column,
            boxpoints='outliers',
            jitter=0.3,
            pointpos=-1.8
        ))
        
        fig.update_layout(
            title=f'Box Plot: {column}',
            yaxis_title=column,
            template='plotly_white'
        )
        
        filename = f'interactive_box_{column}.html'
        filepath = os.path.join(self.output_dir, filename)
        fig.write_html(filepath)
        
        self.plots[f'box_{column}'] = {
            'type': 'box',
            'column': column,
            'path': filename,
            'plot_data': fig.to_json()
        }
    
    def create_3d_scatter_plot(self, numerical_cols):
        """Создание 3D scatter plot с кластеризацией"""
        if len(numerical_cols) < 3:
            print("Недостаточно числовых колонок для 3D scatter plot")
            return
        
        # Выбираем первые 3 числовые переменные
        cols = numerical_cols[:3]
        
        # Простая кластеризация K-means
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            
            # Подготавливаем данные
            data = self.df[cols].dropna()
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(data)
            
            # Кластеризация
            kmeans = KMeans(n_clusters=min(5, len(data)//10), random_state=42)
            clusters = kmeans.fit_predict(scaled_data)
            
            # Создаем 3D график
            fig = go.Figure(data=[go.Scatter3d(
                x=data[cols[0]],
                y=data[cols[1]],
                z=data[cols[2]],
                mode='markers',
                marker=dict(
                    size=8,
                    color=clusters,
                    colorscale='Viridis',
                    opacity=0.7
                ),
                text=[f'Кластер {c}<br>{cols[0]}: {x:.2f}<br>{cols[1]}: {y:.2f}<br>{cols[2]}: {z:.2f}' 
                      for c, x, y, z in zip(clusters, data[cols[0]], data[cols[1]], data[cols[2]])],
                hovertemplate='<b>%{text}</b><extra></extra>'
            )])
            
            fig.update_layout(
                title=f'3D Scatter Plot с кластеризацией: {cols[0]} vs {cols[1]} vs {cols[2]}',
                scene=dict(
                    xaxis_title=cols[0],
                    yaxis_title=cols[1],
                    zaxis_title=cols[2]
                ),
                template='plotly_white'
            )
            
            filename = f'interactive_3d_scatter_{cols[0]}_{cols[1]}_{cols[2]}.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            self.plots[f'3d_scatter_{cols[0]}_{cols[1]}_{cols[2]}'] = {
                'type': '3d_scatter',
                'columns': list(cols),
                'path': filename,
                'plot_data': fig.to_json()
            }
            
        except ImportError:
            print("scikit-learn не установлен, пропускаем 3D кластеризацию")
        except Exception as e:
            print(f"Ошибка при создании 3D scatter plot: {e}")
    
    def create_parallel_coordinates_plot(self, numerical_cols):
        """Создание parallel coordinates plot"""
        if len(numerical_cols) < 2:
            print("Недостаточно числовых колонок для parallel coordinates plot")
            return
        try:
            # Ограничиваем количество переменных для читаемости
            cols = numerical_cols[:min(5, len(numerical_cols))]
            # Используем только строки без NaN во всех нужных колонках
            clean_df = self.df[cols].dropna()
            if clean_df.empty:
                print("Нет данных без пропусков для parallel coordinates plot")
                return
            # Нормализуем данные для лучшей визуализации
            normalized_data = clean_df.copy()
            for col in cols:
                normalized_data[col] = (normalized_data[col] - normalized_data[col].min()) / (normalized_data[col].max() - normalized_data[col].min())
            fig = go.Figure(data=
                go.Parcoords(
                    line = dict(color = normalized_data[cols[0]],
                               colorscale = 'Viridis'),
                    dimensions = [dict(range = [0, 1],
                                     label = col,
                                     values = normalized_data[col]) for col in cols]
                )
            )
            fig.update_layout(
                title='Parallel Coordinates Plot',
                template='plotly_white'
            )
            filename = 'interactive_parallel_coordinates.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            self.plots['parallel_coordinates'] = {
                'type': 'parallel_coordinates',
                'columns': list(cols),
                'path': filename,
                'plot_data': fig.to_json()
            }
        except Exception as e:
            print(f"Ошибка при создании parallel coordinates plot: {e}")
    
    def create_scatter_matrix(self, numerical_cols):
        """Создание интерактивной scatter matrix"""
        if len(numerical_cols) < 3:
            print("Недостаточно числовых колонок для scatter matrix")
            return
        try:
            # Ограничиваем количество переменных
            cols = numerical_cols[:min(4, len(numerical_cols))]
            # Используем только строки без NaN во всех нужных колонках
            clean_df = self.df[cols].dropna()
            if clean_df.empty:
                print("Нет данных без пропусков для scatter matrix")
                return
            fig = px.scatter_matrix(
                clean_df,
                dimensions=cols,
                color=clean_df[cols[0]] if len(cols) > 0 else None,
                title="Scatter Matrix"
            )
            fig.update_layout(
                template='plotly_white',
                height=800
            )
            filename = 'interactive_scatter_matrix.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            self.plots['scatter_matrix'] = {
                'type': 'scatter_matrix',
                'columns': list(cols),
                'path': filename,
                'plot_data': fig.to_json()
            }
        except Exception as e:
            print(f"Ошибка при создании scatter matrix: {e}")
    
    def create_qq_plot(self, column):
        """Создание Q-Q plot для проверки нормальности"""
        try:
            from scipy import stats
            import numpy as np
            
            data = self.df[column].dropna()
            if len(data) < 10:
                return
            
            # Создаем Q-Q plot
            qq_data = stats.probplot(data, dist="norm")
            
            fig = go.Figure()
            
            # Теоретические квантили
            fig.add_trace(go.Scatter(
                x=qq_data[0][0],
                y=qq_data[0][1],
                mode='markers',
                name='Данные',
                marker=dict(color='blue', size=8)
            ))
            
            # Линия нормального распределения (упрощенная)
            # Добавляем только точки без линии для избежания проблем с типами
            
            fig.update_layout(
                title=f'Q-Q Plot: {column}',
                xaxis_title='Теоретические квантили',
                yaxis_title='Эмпирические квантили',
                template='plotly_white'
            )
            
            filename = f'interactive_qq_{column}.html'
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            self.plots[f'qq_{column}'] = {
                'type': 'qq_plot',
                'column': column,
                'path': filename,
                'plot_data': fig.to_json()
            }
            
        except ImportError:
            print("scipy не установлен, пропускаем Q-Q plot")
        except Exception as e:
            print(f"Ошибка при создании Q-Q plot для {column}: {e}")
    
    def save_plots_json(self):
        """Сохранение метаданных графиков в JSON"""
        plots_metadata = {
            'total_plots': len(self.plots),
            'plots': self.plots
        }
        
        filepath = os.path.join(self.output_dir, 'interactive_plots.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(plots_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"Создано {len(self.plots)} интерактивных графиков")
        print(f"Метаданные сохранены в {filepath}") 