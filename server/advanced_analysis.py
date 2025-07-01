#!/usr/bin/env python3
"""
Модуль для продвинутой аналитики данных
Включает статистический анализ, временные ряды, кластеризацию и другие методы
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

class AdvancedDataAnalyzer:
    """Класс для продвинутого анализа данных"""
    
    def __init__(self, df, output_dir, special_columns=None):
        self.df = df.copy()
        self.output_dir = output_dir
        self.analysis_results = {}
        self.special_columns = special_columns or []
        
        # Исключаем специальные столбцы из числовых для статистических вычислений
        self.numerical_cols = [col for col in self.df.select_dtypes(include=[np.number]).columns 
                              if col not in self.special_columns]
        print(f"Числовые столбцы для анализа (исключая специальные): {self.numerical_cols}")
        print(f"Специальные столбцы (исключены из анализа): {self.special_columns}")
        
    def comprehensive_analysis(self):
        """Комплексный анализ данных"""
        print("Запуск комплексного анализа данных...")
        
        # Базовый статистический анализ
        self.basic_statistics()
        
        # Анализ распределений
        self.distribution_analysis()
        
        # Анализ выбросов
        self.outlier_analysis()
        
        # Корреляционный анализ
        self.correlation_analysis()
        
        # Временной анализ (если есть даты)
        self.time_series_analysis()
        
        # Кластерный анализ
        self.clustering_analysis()
        
        # Регрессионный анализ
        self.regression_analysis()
        
        # Анализ категориальных данных
        self.categorical_analysis()
        
        # Генерация инсайтов
        self.generate_insights()
        
        # Генерация отчета
        self.generate_report()
        
        return self.analysis_results
    
    def basic_statistics(self):
        """Базовый статистический анализ"""
        print("Выполнение базового статистического анализа...")
        
        if len(self.numerical_cols) > 0:
            stats_data = {}
            
            for col in self.numerical_cols:
                col_data = self.df[col].dropna()
                if len(col_data) > 0:
                    stats_data[col] = {
                        'count': len(col_data),
                        'mean': col_data.mean(),
                        'median': col_data.median(),
                        'std': col_data.std(),
                        'min': col_data.min(),
                        'max': col_data.max(),
                        'q25': col_data.quantile(0.25),
                        'q75': col_data.quantile(0.75),
                        'skewness': col_data.skew(),
                        'kurtosis': col_data.kurtosis()
                    }
            
            self.analysis_results['basic_stats'] = stats_data
            
            # Создаем сводную таблицу статистик
            stats_df = pd.DataFrame(stats_data).T
            stats_df.to_csv(f"{self.output_dir}/basic_statistics.csv")
            
            # Визуализация статистик
            self._plot_basic_statistics(stats_df)
    
    def distribution_analysis(self):
        """Анализ распределений"""
        print("Анализ распределений...")
        
        for col in self.numerical_cols:
            col_data = self.df[col].dropna()
            if len(col_data) > 0:
                # Гистограмма с кривой плотности
                plt.figure(figsize=(12, 8))
                
                plt.subplot(2, 2, 1)
                plt.hist(col_data, bins=30, alpha=0.7, density=True, color='skyblue', edgecolor='black')
                plt.title(f'Распределение {col}')
                plt.xlabel(col)
                plt.ylabel('Плотность')
                
                # Кривая плотности
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(col_data)
                x_range = np.linspace(col_data.min(), col_data.max(), 100)
                plt.plot(x_range, kde(x_range), 'r-', linewidth=2)
                
                # Q-Q plot
                plt.subplot(2, 2, 2)
                stats.probplot(col_data, dist="norm", plot=plt)
                plt.title(f'Q-Q Plot для {col}')
                
                # Box plot
                plt.subplot(2, 2, 3)
                plt.boxplot(col_data)
                plt.title(f'Box Plot для {col}')
                plt.ylabel(col)
                
                # Violin plot
                plt.subplot(2, 2, 4)
                plt.violinplot(col_data)
                plt.title(f'Violin Plot для {col}')
                plt.ylabel(col)
                
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/distribution_{col}.png", dpi=300, bbox_inches='tight')
                plt.close()
    
    def outlier_analysis(self):
        """Анализ выбросов"""
        print("Анализ выбросов...")
        
        outliers_data = {}
        
        for col in self.numerical_cols:
            col_data = self.df[col].dropna()
            if len(col_data) > 0:
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                
                outliers_data[col] = {
                    'outlier_count': len(outliers),
                    'outlier_percentage': len(outliers) / len(col_data) * 100,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                    'outliers': outliers.tolist()
                }
        
        self.analysis_results['outliers'] = outliers_data
        
        # Визуализация выбросов
        if len(self.numerical_cols) > 0:
            plt.figure(figsize=(15, 10))
            
            for i, col in enumerate(self.numerical_cols[:4], 1):  # Показываем первые 4 столбца
                plt.subplot(2, 2, i)
                col_data = self.df[col].dropna()
                
                plt.boxplot(col_data)
                plt.title(f'Выбросы в {col}')
                plt.ylabel(col)
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/outliers_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def correlation_analysis(self):
        """Расширенный корреляционный анализ"""
        print("Корреляционный анализ...")
        
        if len(self.numerical_cols) > 1:
            # Матрица корреляций
            corr_matrix = self.df[self.numerical_cols].corr()
            
            # Сохраняем матрицу корреляций
            corr_matrix.to_csv(f"{self.output_dir}/correlation_matrix.csv")
            
            # Визуализация
            plt.figure(figsize=(12, 10))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5, cbar_kws={"shrink": .8})
            plt.title('Матрица корреляций')
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/correlation_heatmap.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # Находим сильные корреляции
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # Сильная корреляция
                        strong_correlations.append({
                            'variable1': corr_matrix.columns[i],
                            'variable2': corr_matrix.columns[j],
                            'correlation': corr_value
                        })
            
            self.analysis_results['strong_correlations'] = strong_correlations
    
    def time_series_analysis(self):
        """Анализ временных рядов"""
        print("Анализ временных рядов...")
        
        # Ищем столбцы с датами
        date_cols = []
        for col in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                date_cols.append(col)
        
        if len(date_cols) > 0:
            for date_col in date_cols:
                # Группируем по дате и анализируем числовые столбцы
                numerical_cols = self.df.select_dtypes(include=[np.number]).columns
                
                for num_col in numerical_cols:
                    # Создаем временной ряд
                    time_series = self.df.groupby(date_col)[num_col].mean().sort_index()
                    
                    if len(time_series) > 1:
                        plt.figure(figsize=(15, 10))
                        
                        # Временной ряд
                        plt.subplot(2, 2, 1)
                        plt.plot(time_series.index, time_series.values, marker='o')
                        plt.title(f'Временной ряд: {num_col} по {date_col}')
                        plt.xlabel('Дата')
                        plt.ylabel(num_col)
                        plt.xticks(rotation=45)
                        
                        # Скользящее среднее
                        plt.subplot(2, 2, 2)
                        window_size = min(7, len(time_series) // 4)
                        if window_size > 1:
                            rolling_mean = time_series.rolling(window=window_size).mean()
                            plt.plot(time_series.index, time_series.values, alpha=0.7, label='Исходные данные')
                            plt.plot(rolling_mean.index, rolling_mean.values, 'r-', linewidth=2, label=f'Скользящее среднее (окно={window_size})')
                            plt.title(f'Скользящее среднее для {num_col}')
                            plt.legend()
                            plt.xticks(rotation=45)
                        
                        # Сезонность (если достаточно данных)
                        if len(time_series) > 12:
                            plt.subplot(2, 2, 3)
                            # Анализ по месяцам
                            monthly_data = time_series.groupby(time_series.index.month).mean()
                            plt.bar(monthly_data.index, monthly_data.values)
                            plt.title(f'Сезонность по месяцам: {num_col}')
                            plt.xlabel('Месяц')
                            plt.ylabel(f'Среднее {num_col}')
                        
                        # Автокорреляция
                        plt.subplot(2, 2, 4)
                        from statsmodels.graphics.tsaplots import plot_acf
                        try:
                            plot_acf(time_series.dropna(), lags=min(20, len(time_series)//2), ax=plt.gca())
                            plt.title(f'Автокорреляция для {num_col}')
                        except:
                            plt.text(0.5, 0.5, 'Недостаточно данных для автокорреляции', 
                                   ha='center', va='center', transform=plt.gca().transAxes)
                        
                        plt.tight_layout()
                        plt.savefig(f"{self.output_dir}/timeseries_{num_col}_{date_col}.png", dpi=300, bbox_inches='tight')
                        plt.close()
    
    def clustering_analysis(self):
        """Кластерный анализ"""
        print("Кластерный анализ...")
        
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numerical_cols) >= 2:
            # Подготавливаем данные
            data_for_clustering = self.df[numerical_cols].dropna()
            
            if len(data_for_clustering) > 10:
                # Стандартизация
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(data_for_clustering)
                
                # Определяем оптимальное количество кластеров
                inertias = []
                K_range = range(1, min(11, len(data_for_clustering) // 2))
                
                for k in K_range:
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                    kmeans.fit(scaled_data)
                    inertias.append(kmeans.inertia_)
                
                # График локтя
                plt.figure(figsize=(12, 5))
                plt.subplot(1, 2, 1)
                plt.plot(K_range, inertias, 'bo-')
                plt.xlabel('Количество кластеров')
                plt.ylabel('Инерция')
                plt.title('Метод локтя для определения количества кластеров')
                
                # Кластеризация с оптимальным k
                optimal_k = 3  # По умолчанию
                if len(K_range) > 2:
                    # Простой метод определения локтя
                    diffs = np.diff(inertias)
                    optimal_k = K_range[np.argmin(np.abs(diffs)) + 1]
                
                kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(scaled_data)
                
                # Визуализация кластеров (если 2D или 3D)
                if len(numerical_cols) == 2:
                    plt.subplot(1, 2, 2)
                    scatter = plt.scatter(data_for_clustering.iloc[:, 0], data_for_clustering.iloc[:, 1], 
                                        c=clusters, cmap='viridis')
                    plt.xlabel(numerical_cols[0])
                    plt.ylabel(numerical_cols[1])
                    plt.title(f'Кластеры (k={optimal_k})')
                    plt.colorbar(scatter)
                
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/clustering_analysis.png", dpi=300, bbox_inches='tight')
                plt.close()
                
                # Сохраняем результаты кластеризации
                data_for_clustering['Cluster'] = clusters
                data_for_clustering.to_csv(f"{self.output_dir}/clustering_results.csv")
                
                self.analysis_results['clustering'] = {
                    'optimal_k': optimal_k,
                    'cluster_sizes': data_for_clustering['Cluster'].value_counts().to_dict()
                }
    
    def regression_analysis(self):
        """Регрессионный анализ"""
        print("Регрессионный анализ...")
        
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numerical_cols) >= 2:
            # Простая линейная регрессия между всеми парами переменных
            regression_results = []
            
            for i, target in enumerate(numerical_cols):
                for j, feature in enumerate(numerical_cols):
                    if i != j:
                        # Убираем NaN
                        clean_data = self.df[[target, feature]].dropna()
                        
                        if len(clean_data) > 10:
                            X = clean_data[feature].values.reshape(-1, 1)
                            y = clean_data[target].values
                            
                            # Линейная регрессия
                            model = LinearRegression()
                            model.fit(X, y)
                            
                            # Предсказания
                            y_pred = model.predict(X)
                            
                            # R-squared
                            r_squared = model.score(X, y)
                            
                            # Визуализация
                            plt.figure(figsize=(10, 6))
                            plt.scatter(X, y, alpha=0.6, label='Данные')
                            plt.plot(X, y_pred, 'r-', linewidth=2, label=f'Регрессия (R²={r_squared:.3f})')
                            plt.xlabel(feature)
                            plt.ylabel(target)
                            plt.title(f'Регрессия: {target} vs {feature}')
                            plt.legend()
                            plt.tight_layout()
                            plt.savefig(f"{self.output_dir}/regression_{target}_vs_{feature}.png", dpi=300, bbox_inches='tight')
                            plt.close()
                            
                            regression_results.append({
                                'target': target,
                                'feature': feature,
                                'r_squared': r_squared,
                                'slope': model.coef_[0],
                                'intercept': model.intercept_
                            })
            
            # Сохраняем результаты
            if regression_results:
                reg_df = pd.DataFrame(regression_results)
                reg_df.to_csv(f"{self.output_dir}/regression_analysis.csv", index=False)
                
                # Лучшие модели
                best_models = reg_df.nlargest(5, 'r_squared')
                self.analysis_results['best_regressions'] = best_models.to_dict('records')
    
    def categorical_analysis(self):
        """Анализ категориальных данных"""
        print("Анализ категориальных данных...")
        
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            # Частотный анализ
            value_counts = self.df[col].value_counts()
            
            # Визуализация
            plt.figure(figsize=(12, 8))
            
            # Столбчатая диаграмма
            plt.subplot(2, 2, 1)
            value_counts.plot(kind='bar')
            plt.title(f'Частотный анализ: {col}')
            plt.xlabel(col)
            plt.ylabel('Количество')
            plt.xticks(rotation=45)
            
            # Круговая диаграмма (только топ-10)
            plt.subplot(2, 2, 2)
            top_10 = value_counts.head(10)
            plt.pie(top_10.values, labels=top_10.index, autopct='%1.1f%%')
            plt.title(f'Топ-10 значений: {col}')
            
            # Анализ с числовыми переменными
            numerical_cols = self.df.select_dtypes(include=[np.number]).columns
            if len(numerical_cols) > 0:
                # Box plot для первой числовой переменной
                plt.subplot(2, 2, 3)
                num_col = numerical_cols[0]
                self.df.boxplot(column=num_col, by=col, ax=plt.gca())
                plt.title(f'{num_col} по категориям {col}')
                plt.suptitle('')  # Убираем автоматический заголовок
            
            # Heatmap корреляций (если есть другие категориальные переменные)
            if len(categorical_cols) > 1:
                plt.subplot(2, 2, 4)
                # Создаем dummy variables
                dummy_df = pd.get_dummies(self.df[categorical_cols])
                corr_matrix = dummy_df.corr()
                
                if corr_matrix.shape[0] > 1:
                    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0)
                    plt.title(f'Корреляции категориальных переменных')
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/categorical_analysis_{col}.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # Сохраняем статистики
            stats_data = {
                'unique_values': len(value_counts),
                'most_common': value_counts.index[0],
                'most_common_count': value_counts.iloc[0],
                'least_common': value_counts.index[-1],
                'least_common_count': value_counts.iloc[-1]
            }
            
            self.analysis_results[f'categorical_{col}'] = stats_data
    
    def _plot_basic_statistics(self, stats_df):
        """Визуализация базовых статистик"""
        plt.figure(figsize=(15, 10))
        
        # Средние значения
        plt.subplot(2, 3, 1)
        plt.bar(stats_df.index, stats_df['mean'])
        plt.title('Средние значения')
        plt.xticks(rotation=45)
        
        # Стандартные отклонения
        plt.subplot(2, 3, 2)
        plt.bar(stats_df.index, stats_df['std'])
        plt.title('Стандартные отклонения')
        plt.xticks(rotation=45)
        
        # Асимметрия
        plt.subplot(2, 3, 3)
        plt.bar(stats_df.index, stats_df['skewness'])
        plt.title('Асимметрия')
        plt.xticks(rotation=45)
        plt.axhline(y=0, color='r', linestyle='--')
        
        # Эксцесс
        plt.subplot(2, 3, 4)
        plt.bar(stats_df.index, stats_df['kurtosis'])
        plt.title('Эксцесс')
        plt.xticks(rotation=45)
        plt.axhline(y=0, color='r', linestyle='--')
        
        # Минимальные значения
        plt.subplot(2, 3, 5)
        plt.bar(stats_df.index, stats_df['min'])
        plt.title('Минимальные значения')
        plt.xticks(rotation=45)
        
        # Максимальные значения
        plt.subplot(2, 3, 6)
        plt.bar(stats_df.index, stats_df['max'])
        plt.title('Максимальные значения')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/basic_statistics_plots.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_insights(self):
        """Генерация текстовых инсайтов и рекомендаций на основе анализа"""
        insights = []
        # 1. Выбросы
        outliers = self.analysis_results.get('outliers', {})
        for col, info in outliers.items():
            if info['outlier_count'] > 0:
                insights.append(f"В столбце '{col}' обнаружено {info['outlier_count']} выбросов ({info['outlier_percentage']:.1f}%). Рекомендуется проверить эти значения.")
        # 2. Сильные корреляции
        strong_corrs = self.analysis_results.get('strong_correlations', [])
        for corr in strong_corrs:
            insights.append(f"Между '{corr['variable1']}' и '{corr['variable2']}' обнаружена сильная корреляция ({corr['correlation']:.2f}). Возможно, эти переменные связаны.")
        # 3. Асимметрия и эксцесс
        basic_stats = self.analysis_results.get('basic_stats', {})
        for col, stats in basic_stats.items():
            if abs(stats.get('skewness', 0)) > 1:
                insights.append(f"Распределение '{col}' сильно асимметрично (асимметрия = {stats['skewness']:.2f}).")
            if abs(stats.get('kurtosis', 0)) > 3:
                insights.append(f"Распределение '{col}' имеет выраженные хвосты (эксцесс = {stats['kurtosis']:.2f}).")
        # 4. Категориальные переменные
        for key in self.analysis_results:
            if key.startswith('categorical_'):
                cat = self.analysis_results[key]
                if cat['unique_values'] > 20:
                    insights.append(f"В категориальной переменной '{key[12:]}' много уникальных значений ({cat['unique_values']}).")
                else:
                    insights.append(f"В категориальной переменной '{key[12:]}' наиболее часто встречается '{cat['most_common']}' ({cat['most_common_count']} раз).")
        # 5. Кластеры
        clustering = self.analysis_results.get('clustering', None)
        if clustering:
            insights.append(f"Данные можно разделить на {clustering['optimal_k']} кластера(ов). Самый крупный кластер содержит {max(clustering['cluster_sizes'].values())} объектов.")
        # 6. Регрессии
        best_regs = self.analysis_results.get('best_regressions', [])
        used_pairs = set()
        for reg in best_regs:
            if reg['r_squared'] > 0.7:
                pair = frozenset([reg['feature'], reg['target']])
                if pair in used_pairs:
                    continue
                used_pairs.add(pair)
                insights.append(f"Между '{reg['feature']}' и '{reg['target']}' обнаружена сильная линейная зависимость (R² = {reg['r_squared']:.2f}).")
        # 7. Общие рекомендации
        if not insights:
            insights.append("Данные не содержат явных аномалий или сильных связей. Рекомендуется провести более глубокий анализ.")
        self.analysis_results['insights'] = insights
        return insights
    
    def generate_report(self):
        """Генерация текстового отчета"""
        print("Генерация отчета...")
        
        report = []
        report.append("# АНАЛИТИЧЕСКИЙ ОТЧЕТ")
        report.append("=" * 50)
        report.append(f"Дата анализа: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Размер данных: {self.df.shape[0]} строк, {self.df.shape[1]} столбцов")
        report.append("")
        
        # Основные выводы
        if 'basic_stats' in self.analysis_results:
            report.append("## ОСНОВНЫЕ СТАТИСТИКИ")
            report.append("-" * 30)
            for col, stats in self.analysis_results['basic_stats'].items():
                report.append(f"**{col}:**")
                report.append(f"  - Среднее: {stats['mean']:.2f}")
                report.append(f"  - Медиана: {stats['median']:.2f}")
                report.append(f"  - Стандартное отклонение: {stats['std']:.2f}")
                report.append(f"  - Минимум: {stats['min']:.2f}")
                report.append(f"  - Максимум: {stats['max']:.2f}")
                report.append("")
        
        # Выбросы
        if 'outliers' in self.analysis_results:
            report.append("## АНАЛИЗ ВЫБРОСОВ")
            report.append("-" * 30)
            for col, outlier_info in self.analysis_results['outliers'].items():
                if outlier_info['outlier_count'] > 0:
                    report.append(f"**{col}:** {outlier_info['outlier_count']} выбросов ({outlier_info['outlier_percentage']:.1f}%)")
            report.append("")
        
        # Сильные корреляции
        if 'strong_correlations' in self.analysis_results:
            report.append("## СИЛЬНЫЕ КОРРЕЛЯЦИИ")
            report.append("-" * 30)
            for corr in self.analysis_results['strong_correlations']:
                report.append(f"**{corr['variable1']}** и **{corr['variable2']}**: {corr['correlation']:.3f}")
            report.append("")
        
        # Лучшие регрессии
        if 'best_regressions' in self.analysis_results:
            report.append("## ЛУЧШИЕ РЕГРЕССИОННЫЕ МОДЕЛИ")
            report.append("-" * 30)
            for reg in self.analysis_results['best_regressions']:
                report.append(f"**{reg['target']}** = {reg['slope']:.3f} × **{reg['feature']}** + {reg['intercept']:.3f} (R² = {reg['r_squared']:.3f})")
            report.append("")
        
        # Кластеризация
        if 'clustering' in self.analysis_results:
            report.append("## КЛАСТЕРНЫЙ АНАЛИЗ")
            report.append("-" * 30)
            report.append(f"Оптимальное количество кластеров: {self.analysis_results['clustering']['optimal_k']}")
            report.append("Размеры кластеров:")
            for cluster, size in self.analysis_results['clustering']['cluster_sizes'].items():
                report.append(f"  - Кластер {cluster}: {size} объектов")
            report.append("")
        
        # Рекомендации
        report.append("## РЕКОМЕНДАЦИИ")
        report.append("-" * 30)
        
        # Анализируем данные и даем рекомендации
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        
        if len(numerical_cols) > 0:
            report.append("### Для числовых переменных:")
            for col in numerical_cols:
                col_data = self.df[col].dropna()
                if len(col_data) > 0:
                    skewness = col_data.skew()
                    if abs(skewness) > 1:
                        report.append(f"- **{col}**: Распределение асимметрично (асимметрия = {skewness:.2f})")
                    if 'outliers' in self.analysis_results and col in self.analysis_results['outliers']:
                        outlier_pct = self.analysis_results['outliers'][col]['outlier_percentage']
                        if outlier_pct > 5:
                            report.append(f"- **{col}**: Обнаружено много выбросов ({outlier_pct:.1f}%)")
        
        if len(categorical_cols) > 0:
            report.append("### Для категориальных переменных:")
            for col in categorical_cols:
                unique_count = self.df[col].nunique()
                total_count = len(self.df[col])
                if unique_count > total_count * 0.8:
                    report.append(f"- **{col}**: Много уникальных значений ({unique_count}), возможно стоит рассмотреть как числовую переменную")
        
        # Сохраняем отчет
        with open(f"{self.output_dir}/analysis_report.md", 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"Отчет сохранен в {self.output_dir}/analysis_report.md") 