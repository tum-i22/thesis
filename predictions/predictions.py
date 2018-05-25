import sys
import json
import os
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegressionCV
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import label_binarize
from sklearn import svm
from sklearn.metrics import roc_curve, auc
from lib.pycvss3 import CVSS3
import numpy
from sklearn.model_selection import train_test_split
from sklearn import metrics

# We need only the values for CVSS3 scores of the resulting array NODEATTRIBUTES + CVSS3
def prep_data(function_data):
    cvss3_data = []
    node_attributes = []
    for key, value in sorted(function_data.items()):
        if key == 'clustering_coefficient':
            node_attributes.append(value)
        elif key == 'cvss3':
            cvss3_data = value
        elif key == 'distance_to_interface':
            node_attributes.append(value)
        elif key == 'macke_bug_chain_length':
            node_attributes.append(value)
        elif key == 'macke_vulnerabilities_found':
            node_attributes.append(value)
        elif key == 'node_degree':
            node_attributes.append(value[2])
        elif key == 'node_path_length':
            node_attributes.append(value)
        elif key == 'n_pointer_args':
            node_attributes.append(value)
        elif key == 'function_length':
            node_attributes.append(value)
        elif key == 'n_blocks':
            node_attributes.append(value)

    # Mapping CVSS3 values
    for cvss3_entry_key, cvss3_entry_data in sorted(cvss3_data.items()):
        if cvss3_entry_key == 'attackVector':
            if cvss3_entry_data == 'NETWORK':
                y_attack_vector.append(0)
            elif cvss3_entry_data == 'ADJACENT':
                y_attack_vector.append(1)
            elif cvss3_entry_data == 'LOCAL':
                y_attack_vector.append(2)
            elif cvss3_entry_data == 'PHYSICAL':
                y_attack_vector.append(3)
        elif cvss3_entry_key == 'attackComplexity':
            if cvss3_entry_data == 'LOW':
                y_attack_complexity.append(0)
            elif cvss3_entry_data == 'HIGH':
                y_attack_complexity.append(1)
        elif cvss3_entry_key == 'privilegesRequired':
            if cvss3_entry_data == 'NONE':
                y_privileges_required.append(0)
            elif cvss3_entry_data == 'LOW':
                y_privileges_required.append(1)
            elif cvss3_entry_data == 'HIGH':
                y_privileges_required.append(2)
        elif cvss3_entry_key == 'userInteraction':
            if cvss3_entry_data == 'NONE':
                y_user_interaction.append(0)
            elif cvss3_entry_data == 'REQUIRED':
                y_user_interaction.append(1)
        elif cvss3_entry_key == 'scope':
            if cvss3_entry_data == 'UNCHANGED':
                y_scope.append(0)
            elif cvss3_entry_data == 'CHANGED':
                y_scope.append(1)
        elif cvss3_entry_key == 'confidentialityImpact':
            if cvss3_entry_data == 'NONE':
                y_confidentiality_impact.append(0)
            elif cvss3_entry_data == 'LOW':
                y_confidentiality_impact.append(1)
            elif cvss3_entry_data == 'HIGH':
                y_confidentiality_impact.append(2)
        elif cvss3_entry_key == 'integrityImpact':
            if cvss3_entry_data == 'NONE':
                y_integrity_impact.append(0)
            elif cvss3_entry_data == 'LOW':
                y_integrity_impact.append(1)
            elif cvss3_entry_data == 'HIGH':
                y_integrity_impact.append(2)
        elif cvss3_entry_key == 'availabilityImpact':
            if cvss3_entry_data == 'NONE':
                y_availability_impact.append(0)
            elif cvss3_entry_data == 'LOW':
                y_availability_impact.append(1)
            elif cvss3_entry_data == 'HIGH':
                y_availability_impact.append(2)
    X.append(node_attributes)



def generate_cvss3_object(av, ac, p, ui, s, c, i, ai):
    cvss3 = {}
    cvss3['vectorString'] = ''
    if av.item() == 0:
        cvss3['attackVector'] = 'NETWORK'
        cvss3['vectorString'] += ('AV:N')
    elif av.item() == 1:
        cvss3['attackVector'] = 'ADJACENT'
        cvss3['vectorString'] += ('AV:A')
    elif av.item() == 2:
        cvss3['attackVector'] = 'LOCAL'
        cvss3['vectorString'] += ('AV:L')
    elif av.item() == 3:
        cvss3['attackVector'] = 'PHYSICAL'
        cvss3['vectorString'] += ('AV:P')

    if ac.item() == 0:
        cvss3['attackComplexity'] = 'LOW'
        cvss3['vectorString'] += ('/AC:L')
    elif ac.item() == 1:
        cvss3['attackComplexity'] = 'HIGH'
        cvss3['vectorString'] += ('/AC:H')

    if p.item() == 0:
        cvss3['privilegesRequired'] = 'NONE'
        cvss3['vectorString'] += ('/PR:N')
    elif p.item() == 1:
        cvss3['privilegesRequired'] = 'LOW'
        cvss3['vectorString'] += ('/PR:L')
    elif p.item() == 2:
        cvss3['privilegesRequired'] = 'HIGH'
        cvss3['vectorString'] += ('/PR:H')

    if ui.item() == 0:
        cvss3['userInteraction'] = 'NONE'
        cvss3['vectorString'] += ('/UI:N')
    elif ui.item() == 1:
        cvss3['userInteraction'] = 'REQUIRED'
        cvss3['vectorString'] += ('/UI:R')

    if s.item() == 0:
        cvss3['scope'] = 'UNCHANGED'
        cvss3['vectorString'] += ('/S:U')
    elif s.item() == 1:
        cvss3['scope'] = 'CHANGED'
        cvss3['vectorString'] += ('/S:C')

    if c.item() == 0:
        cvss3['confidentialityImpact'] = 'NONE'
        cvss3['vectorString'] += ('/C:N')
    elif c.item() == 1:
        cvss3['confidentialityImpact'] = 'LOW'
        cvss3['vectorString'] += ('/C:L')
    elif c.item() == 2:
        cvss3['confidentialityImpact'] = 'HIGH'
        cvss3['vectorString'] += ('/C:H')

    if i.item() == 0:
        cvss3['integrityImpact'] = 'NONE'
        cvss3['vectorString'] += ('/I:N')
    elif i.item() == 1:
        cvss3['integrityImpact'] = 'LOW'
        cvss3['vectorString'] += ('/I:L')
    elif i.item() == 2:
        cvss3['integrityImpact'] = 'HIGH'
        cvss3['vectorString'] += ('/I:H')

    if ai.item() == 0:
        cvss3['availabilityImpact'] = 'NONE'
        cvss3['vectorString'] += ('/A:N')
    elif ai.item() == 1:
        cvss3['availabilityImpact'] = 'LOW'
        cvss3['vectorString'] += ('/A:L')
    elif ai.item() == 2:
        cvss3['availabilityImpact'] = 'HIGH'
        cvss3['vectorString'] += ('/A:H')

    cvss3_base_score_details = CVSS3(cvss3['vectorString']).cvss_base_score()
    cvss3['baseScore'] = cvss3_base_score_details[0]
    cvss3['baseSeverity'] = cvss3_base_score_details[1].capitalize()
    cvss3['predicted'] = True
    return cvss3


def split_data(X, Y, testdatasize):
    
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=testdatasize)

    #x_train, x_test = X[:34], X[35:]
    #y_train, y_test = Y[:34], Y[35:]

    return x_train, x_test, y_train, y_test



def evaluate_best_learner(x, y, kf, est):
    best_score = 0

    for train, test in kf.split(x):

        X_train, X_test = x[train], x[test]
        y_train, y_test = y[train], y[test]

        #create classifier
        estimator = est.__name__
        # GaussianNB doesnt have class_weight options , so the exception
        if estimator is 'GaussianNB':
            learner = est()
        elif estimator is 'LogisticRegressionCV':
            learner = est(solver='liblinear', class_weight='balanced')
        else:
            learner = est(class_weight='balanced')

        learner.fit(X_train, y_train)

        prediction = learner.predict(X_test)
        score = metrics.accuracy_score(y_test, prediction)

        #print(score)

        if score > best_score:
            best_score = score
            best_learner = learner

    return best_learner



def compute_roc_auc(x_train, x_test, y_train, y_test, est, n_classes):
    # create classifier
    estimator = est.__name__
    # GaussianNB doesnt have class_weight options , so the exception
    if estimator is 'GaussianNB':
        learner = est()
    elif estimator is 'LogisticRegressionCV':
        learner = est(solver='liblinear', class_weight='balanced')
    else:
        learner = est(class_weight='balanced')

    print(y_train.shape)
    y_score = learner.fit(x_train, y_train).predict(x_test)

    roc_auc1 = metrics.roc_auc_score(y_test, y_score, average='micro')

    """

    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Compute micro-average ROC curve and ROC area
    fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), y_score.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    print(roc_auc)
    """

    return roc_auc1


#trial function for OnevsRestClassifier for random forest, generalize later
def roc_one_vs_rest_rf(x_train, x_test, y_train, y_test, est, n_classes):

    classifier = OneVsRestClassifier(RandomForestClassifier(class_weight='balanced'))
    y_score = classifier.fit(x_train, y_train).predict_proba(x_test)

    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Compute micro-average ROC curve and ROC area
    fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), y_score.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    print(roc_auc)







def predict_scores(est, X, Y, testdatasize, kf, y_class):
    #split X and Y
    X_train, X_test, y_train, y_test = split_data(X, Y, testdatasize)

    best_learner = evaluate_best_learner (X_train, y_train, kf, est)
    prediction = best_learner.predict(X_test)
    acc_score = metrics.accuracy_score(y_test, prediction)

    #binarize data for calculating roc auc
    y_bin_train = label_binarize(y_train, y_class)
    y_bin_test = label_binarize(y_test, y_class)

    n_classes = y_bin_test.shape[1]

    #roc_auc = compute_roc_auc(X_train, X_test, y_bin_train, y_bin_test, est, n_classes)
    roc_auc = compute_roc_auc(X_train, X_test, y_train, y_test, est, n_classes)

    #roc_auc = roc_one_vs_rest_rf(X_train, X_test, y_bin_train, y_bin_test, est, n_classes)

    return acc_score, roc_auc



# Main
if len(sys.argv) < 2:
    sys.stderr.write('Syntax : python3 %s /node_attributes_directory\n' % sys.argv[0])
else:
    X = []
    y_attack_vector = []
    y_attack_complexity = []
    y_privileges_required = []
    y_user_interaction = []
    y_scope = []
    y_confidentiality_impact = []
    y_integrity_impact = []
    y_availability_impact = []
    files = os.listdir(sys.argv[1])
    data = []
    prediction_set = []
    structure_data = []
    for file in files:
        with open(os.path.join(sys.argv[1], file)) as data_file:
            all_functions = json.load(data_file)
            for key, value in all_functions.items():
                if value['faulty'] is True:
                    data.append(value)
                else:
                    prediction_set.append({key: value})

    for function in data:
        structure_data.append(prep_data(function))
    print("Shape of X: %d x %d"%(len(X), len(X[0])))


    
    # Convert everything to numpy array
    X = numpy.asarray(X)
    y_attack_vector = numpy.asarray(y_attack_vector)
    y_attack_complexity = numpy.asarray(y_attack_complexity)
    y_privileges_required = numpy.asarray(y_privileges_required)
    y_user_interaction = numpy.asarray(y_user_interaction)
    y_scope = numpy.asarray(y_scope)
    y_integrity_impact = numpy.asarray(y_integrity_impact)
    y_confidentiality_impact = numpy.asarray(y_confidentiality_impact)
    y_availability_impact = numpy.asarray(y_availability_impact)


    # TO_DO make a function to generate these classes looking at y
    y_attack_vector_class = [0, 1, 2, 3]
    y_attack_complexity_class = [0, 1]
    y_privileges_required_class = [0, 1, 2]
    y_user_interaction_class = [0,1]
    y_scope_class = [0, 1]
    y_confidentiality_impact_class = y_integrity_impact_class = y_availability_impact_class = [0,1,2]




    
    testsize = 0.2
    kf = KFold(n_splits=3)

    rf_av_score, rf_av_roc_auc = predict_scores(RandomForestClassifier, X, y_attack_vector, testsize, kf,
                                 y_attack_vector_class)
    rf_ac_score , rf_ac_roc_auc = predict_scores(RandomForestClassifier, X, y_attack_complexity, testsize, kf,
                                                 y_attack_complexity_class)
    rf_pr_score , rf_pr_roc_auc = predict_scores(RandomForestClassifier, X, y_privileges_required, testsize, kf,
                                                 y_privileges_required_class)
    rf_ui_score , rf_ui_roc_auc = predict_scores(RandomForestClassifier, X, y_user_interaction, testsize, kf,
                                                 y_user_interaction_class)
    #rf_sc_score , rf_sc_roc_auc = predict_scores(RandomForestClassifier, X, y_scope, testsize, kf, y_scope_class)
    rf_ii_score , rf_ii_roc_auc = predict_scores(RandomForestClassifier, X, y_integrity_impact,testsize, kf,
                                                 y_integrity_impact_class)
    rf_ci_score , rf_ci_roc_auc = predict_scores(RandomForestClassifier, X, y_confidentiality_impact, testsize, kf,
                                                 y_confidentiality_impact_class)
    rf_ai_score , rf_ai_roc_auc = predict_scores(RandomForestClassifier, X, y_availability_impact, testsize, kf,
                                                 y_availability_impact_class)

    print("========================================")
    print("   RF: ACCURACY SCORES AND ROC AUC")
    print("========================================")
    print("AV: %1.2f           %1.2f" % (rf_av_score, rf_av_roc_auc))
    print("AC: %1.2f           %1.2f" % (rf_ac_score, rf_ac_roc_auc))
    print("P : %1.2f           %1.2f" % (rf_pr_score, rf_pr_roc_auc))
    print("UI: %1.2f           %1.2f" % (rf_ui_score, rf_ui_roc_auc))
    # print("S : %1.2f           "%(rf_s_score))
    print("CI: %1.2f           %1.2f" % (rf_ci_score, rf_ci_roc_auc))
    print("I : %1.2f           %1.2f" % (rf_ii_score, rf_ii_roc_auc))
    print("AI: %1.2f           %1.2f" % (rf_ai_score, rf_ai_roc_auc))
    

    """
    # GaussianNB
    gnb_av_score , gnb_av_roc_auc = predict_scores(GaussianNB, X, y_attack_vector, testsize, kf, y_attack_vector_class)
    gnb_ac_score , gnb_ac_roc_auc = predict_scores(GaussianNB, X, y_attack_complexity, testsize, kf, y_attack_complexity_class)
    gnb_pr_score , gnb_pr_roc_auc = predict_scores(GaussianNB, X, y_privileges_required, testsize, kf, y_privileges_required_class)
    gnb_ui_score , gnb_ui_roc_auc = predict_scores(GaussianNB, X, y_user_interaction, testsize, kf, y_user_interaction_class)
    gnb_ci_score , gnb_ci_roc_auc = predict_scores(GaussianNB, X, y_confidentiality_impact, testsize, kf, y_confidentiality_impact_class)
    #gnb_s_score = predict_scores(GaussianNB, X, y_scope, testsize, kf)
    gnb_ii_score , gnb_ii_roc_auc = predict_scores(GaussianNB, X, y_integrity_impact, testsize,kf, y_integrity_impact_class)
    gnb_ai_score , gnb_ai_roc_auc = predict_scores(GaussianNB, X, y_availability_impact, testsize, kf, y_availability_impact_class)

    print("========================================")
    print("   GNB: ACCURACY SCORES AND ROC AUC")
    print("========================================")
    print("AV: %1.2f           %1.2f" % (gnb_av_score, gnb_av_roc_auc))
    print("AC: %1.2f           %1.2f" % (gnb_ac_score, gnb_ac_roc_auc))
    print("P : %1.2f           %1.2f" % (gnb_pr_score, gnb_pr_roc_auc))
    print("UI: %1.2f           %1.2f" % (gnb_ui_score, gnb_ui_roc_auc))
    # print("S : %1.2f         %1.2f " %(gnb_s_score))
    print("CI: %1.2f           %1.2f" % (gnb_ci_score, gnb_ci_roc_auc))
    print("I : %1.2f           %1.2f" % (gnb_ii_score, gnb_ii_roc_auc))
    print("AI: %1.2f           %1.2f" % (gnb_ai_score, gnb_ai_roc_auc))
    


    # linearSVC

    lsvc_av_score, lsvc_av_roc_auc = predict_scores(LinearSVC, X, y_attack_vector, testsize, kf,
                                                    y_attack_vector_class)
    lsvc_ac_score, lsvc_ac_roc_auc = predict_scores(LinearSVC, X, y_attack_complexity, testsize, kf,
                                   y_attack_complexity_class)
    lsvc_pr_score, lsvc_pr_roc_auc = predict_scores(LinearSVC, X, y_privileges_required, testsize, kf,
                                   y_privileges_required_class)
    lsvc_ui_score, lsvc_ui_roc_auc = predict_scores(LinearSVC, X, y_user_interaction, testsize, kf,
                                   y_user_interaction_class)
    lsvc_ci_score, lsvc_ci_roc_auc = predict_scores(LinearSVC, X, y_confidentiality_impact, testsize, kf,
                                   y_confidentiality_impact_class)
    #lsvc_s_score = predict_scores(LinearSVC,X, y_scope, testsize, kf)
    lsvc_ii_score, lsvc_ii_roc_auc = predict_scores(LinearSVC, X, y_integrity_impact, testsize, kf,
                                   y_integrity_impact_class)
    lsvc_ai_score, lsvc_ai_roc_auc = predict_scores(LinearSVC, X, y_availability_impact, testsize, kf,
                                   y_availability_impact_class)
    
    print("========================================")
    print("   LSVC: ACCURACY SCORES AND ROC AUC")
    print("========================================")
    print("AV: %1.2f           %1.2f" % (lsvc_av_score, lsvc_av_roc_auc))
    print("AC: %1.2f           %1.2f" % (lsvc_ac_score, lsvc_ac_roc_auc))
    print("P : %1.2f           %1.2f" % (lsvc_pr_score, lsvc_pr_roc_auc))
    print("UI: %1.2f           %1.2f" % (lsvc_ui_score, lsvc_ui_roc_auc))
    # print("S : %1.2f         %1.2f " %(lsvc_s_score))
    print("CI: %1.2f           %1.2f" % (lsvc_ci_score, lsvc_ci_roc_auc))
    print("I : %1.2f           %1.2f" % (lsvc_ii_score, lsvc_ii_roc_auc))
    print("AI: %1.2f           %1.2f" % (lsvc_ai_score, lsvc_ai_roc_auc))


    #Logistic Regression CV
    
    lrcv_av_score = predict_scores(LogisticRegressionCV, X, y_attack_vector, testsize, kf)
    lrcv_ac_score = predict_scores(LogisticRegressionCV, X, y_attack_complexity, testsize, kf)
    lrcv_pr_score = predict_scores(LogisticRegressionCV, X, y_privileges_required, testsize, kf)
    lrcv_ui_score = predict_scores(LogisticRegressionCV, X, y_user_interaction, testsize, kf)
    lrcv_ci_score = predict_scores(LogisticRegressionCV, X, y_confidentiality_impact, testsize, kf)
    lrcv_s_score = predict_scores(LogisticRegressionCV, X, y_scope, testsize, kf)
    lrcv_ii_score = predict_scores(LogisticRegressionCV, X, y_integrity_impact, testsize, kf)
    lrcv_ai_score = predict_scores(LogisticRegressionCV, X, y_availability_impact, testsize, kf)

    print("========================================")
    print("   LRCV: ACCURACY SCORES AND ROC AUC")
    print("========================================")
    print("AV: %1.2f           " % (lrcv_av_score))
    print("AC: %1.2f           " % (lrcv_ac_score))
    print("P : %1.2f           " % (lrcv_pr_score))
    print("UI: %1.2f           " % (lrcv_ui_score))
    #print("S : %1.2f           " % (lrcv_s_score))
    print("CI: %1.2f           " % (lrcv_ci_score))
    print("I : %1.2f           " % (lrcv_ii_score))
    print("AI: %1.2f           " % (lrcv_ai_score))
    """


