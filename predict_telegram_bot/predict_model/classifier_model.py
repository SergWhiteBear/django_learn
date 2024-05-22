import pickle
import pandas as pd
from imblearn.over_sampling import SMOTE
from matplotlib import pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, roc_curve

# Пути к файлам с данными
file_path_school = 'C:\\Users\\Sergey\\Desktop\\djangoStudy\\django_predict\\predict_telegram_bot\\data\\БаллыЕГЭ.xlsx'

# Загрузка данных
df = pd.concat(pd.read_excel(file_path_school, sheet_name=None), ignore_index=True)
df_new = pd.concat(pd.read_excel(file_path_school, sheet_name=None), ignore_index=True)

# Обработка пропущенных значений
df['exam_physic'] = df['exam_physic'].fillna(0)
df['exam_inf'] = df['exam_inf'].fillna(0)
df_new['exam_physic'] = df_new['exam_physic'].fillna(0)
df_new['exam_inf'] = df_new['exam_inf'].fillna(0)

# Определение целевой переменной
df['успешность'] = df['Рейтинг'] > 60
df_new['успешность'] = df_new['Рейтинг'] > 60

# Выбор признаков
features = ['total_score', 'exam_math', 'phy_or_inf', 'exam_rus', 'extra_score']

# Добавление новых признаков
# 1. Средний балл по всем экзаменам
df['avg_exam_score'] = df[['exam_math', 'exam_inf', 'exam_physic', 'exam_rus']].mean(axis=1)
df_new['avg_exam_score'] = df_new[['exam_math', 'exam_inf', 'exam_physic', 'exam_rus']].mean(axis=1)

# 2. Количество экзаменов, сданных выше определенного балла (например, 70 баллов)
threshold_score = 70
df['exams_above_threshold'] = (df[['exam_math', 'exam_inf', 'exam_physic', 'exam_rus']] > threshold_score).sum(axis=1)
df_new['exams_above_threshold'] = (df_new[['exam_math', 'exam_inf', 'exam_physic', 'exam_rus']] > threshold_score).sum(axis=1)

# Обновленный список признаков
features += ['avg_exam_score', 'exams_above_threshold']

# Разделение данных на обучающую и тестовую выборки
X = df[features]
y = df['успешность']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Применение SMOTE для балансировки данных (если нужно)
# smote = SMOTE(random_state=42)
# X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

# Стандартизация данных
scaler = StandardScaler()
X_train_balanced = scaler.fit_transform(X_train)
pickle.dump(scaler, open('scaler_fit.pkl', 'wb'))
X_test = scaler.transform(X_test)


# Инициализация модели GradientBoostingClassifier
best_gb = GradientBoostingClassifier(learning_rate=0.05, max_depth=6, max_features='sqrt', n_estimators=150)

best_gb.fit(X_train_balanced, y_train)

# Сохранение scaler и модели в файлы
pickle.dump(scaler, open('scaler_fit.pkl', 'wb'))
pickle.dump(best_gb, open('best_gradient_boosting_model.pkl', 'wb'))


# Оценка и вывод результатов модели на тестовой выборке
y_pred = best_gb.predict(X_test)

# Оценка точности модели с измененным порогом
metrics_gb_threshold = {
    'accuracy': accuracy_score(y_test, y_pred),
    'precision': precision_score(y_test, y_pred),
    'recall': recall_score(y_test, y_pred),
    'f1': f1_score(y_test, y_pred)
}

print('Gradient Boosting Metrics with Adjusted Threshold:')
print(f"Accuracy: {metrics_gb_threshold['accuracy']:.2f}")
print(f"Precision: {metrics_gb_threshold['precision']:.2f}")
print(f"Recall: {metrics_gb_threshold['recall']:.2f}")
print(f"F1-score: {metrics_gb_threshold['f1']:.2f}")

# roc_auc график и оценка модели для модели до добавления новых признаков
y_prob_before = best_gb.predict_proba(X_test)[:, 1]
fpr_before, tpr_before, thresholds_before = roc_curve(y_test, y_prob_before)
roc_auc_before = roc_auc_score(y_test, y_prob_before)

# График для модели до добавления новых признаков
plt.figure()
plt.plot(fpr_before, tpr_before, color='blue', lw=2, label='ROC curve before feature engineering (area = %0.2f)' % roc_auc_before)
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic - Before Feature Engineering')
plt.legend(loc="lower right")
plt.show()

# roc_auc график и оценка модели для модели после добавления новых признаков
y_prob_after = best_gb.predict_proba(X_test)[:, 1]
fpr_after, tpr_after, thresholds_after = roc_curve(y_test, y_prob_after)
roc_auc_after = roc_auc_score(y_test, y_prob_after)

# График для модели после добавления новых признаков
plt.figure()
plt.plot(fpr_after, tpr_after, color='red', lw=2, label='ROC curve after feature engineering (area = %0.2f)' % roc_auc_after)
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic - After Feature Engineering')
plt.legend(loc="lower right")
plt.show()