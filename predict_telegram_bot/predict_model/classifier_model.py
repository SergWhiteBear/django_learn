import pickle
import pandas as pd

from matplotlib import pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, \
    confusion_matrix, roc_auc_score, roc_curve

file_path_standart = 'C:\\Users\\Sergey\\Desktop\\djangoStudy\\django_predict\\predict_telegram_bot\\data\\БаллыЕГЭ.xlsx'


def fit_model(file_path=file_path_standart):
    # Загрузка данных
    df = pd.concat(pd.read_excel(file_path, sheet_name=None), ignore_index=True)
    # Обработка пропущенных значений
    df['exam_physic'] = df['exam_physic'].fillna(0)
    df['exam_inf'] = df['exam_inf'].fillna(0)
    df['total_score'] = df['total_score'].fillna(0)

    # Определение целевой переменной
    df['успешность'] = df['Рейтинг'] > 60

    # Выбор признаков
    features = ['exam_score', 'exam_math', 'exam_inf', 'exam_physic', 'exam_rus', 'extra_score']

    # Добавление новых признаков
    # 1. Средний балл по всем экзаменам
    df['avg_exam_score'] = df[['exam_math', 'exam_inf', 'exam_physic', 'exam_rus']].mean(axis=1)

    # 2. Количество экзаменов, сданных выше определенного балла (например, 70 баллов)
    threshold_score = 70
    df['exams_above_threshold'] = (df[['exam_math', 'exam_inf', 'exam_physic', 'exam_rus']] > threshold_score).sum(
        axis=1)

    # Обновленный список признаков
    features += ['avg_exam_score', 'exams_above_threshold']

    # Разделение данных на обучающую и тестовую выборки
    x = df[features]
    y = df['успешность']
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)

    # Стандартизация данных
    scaler = StandardScaler()
    x_train_scaler = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)

    param_grid = {
        'n_estimators': [200, 300, 400],
        'max_depth': [3, 6, 9],
        'max_features': ['sqrt', 'log2'],
        'min_samples_split': [3, 4, 5],
        'min_samples_leaf': [1, 3, 5],
        'random_state': [42]
    }
    # 'max_depth': 3, 'max_features': 'sqrt', 'min_samples_leaf': 3, 'min_samples_split': 3, 'n_estimators': 400, 'random_state': 42
    # learning_rate=0.05, max_depth=6, max_features='sqrt', n_estimators=150
    # {'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 400}
    # Инициализация GridSearchCV
    grid_search = GridSearchCV(GradientBoostingClassifier(), param_grid, cv=5, scoring='accuracy', n_jobs=-1)

    # Обучение модели с использованием GridSearchCV
    grid_search.fit(x_train_scaler, y_train)

    # Получение лучших параметров
    best_params = grid_search.best_params_
    print(f"Best parameters found: {best_params}")

    # Обучение модели с лучшими параметрами
    best_rf = GradientBoostingClassifier(**best_params)
    best_rf.fit(x_train_scaler, y_train)

    # Сохранение scaler и модели в файлы
    pickle.dump(scaler, open('scaler_fit.pkl', 'wb'))
    pickle.dump(best_rf, open('best_gradient_boosting_model.pkl', 'wb'))

    # Оценка и вывод результатов модели на тестовой выборке
    y_pred = best_rf.predict(x_test)

    # Оценка точности модели с измененным порогом
    metrics_gb = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred)
    }

    print('Gradient Boosting Metrics')
    print(f"Accuracy: {metrics_gb['accuracy']:.2f}")
    print(f"Precision: {metrics_gb['precision']:.2f}")
    print(f"Recall: {metrics_gb['recall']:.2f}")
    print(f"F1-score: {metrics_gb['f1']:.2f}")
    print(f"Classification report:\n{classification_report(y_test, y_pred)}")
    print(f"Confusion matrix:\n{confusion_matrix(y_test, y_pred)}")
    # roc_auc график и оценка модели
    y_prob_after = best_rf.predict_proba(x_test)[:, 1]
    fpr_after, tpr_after, thresholds_after = roc_curve(y_test, y_prob_after)
    roc_auc_after = roc_auc_score(y_test, y_prob_after)

    # График для модели
    plt.figure()
    plt.plot(fpr_after, tpr_after, color='red', lw=2,
             label='ROC curve after feature engineering (area = %0.2f)' % roc_auc_after)
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic - After Feature Engineering')
    plt.legend(loc="lower right")
    plt.show()


def run(file_path):
    fit_model(file_path)
