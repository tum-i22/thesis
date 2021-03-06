import sys, time, random
import json
import os, glob
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
from sklearn.utils import shuffle, class_weight

# We need only the values for CVSS3 scores of the resulting array NODEATTRIBUTES + CVSS3
def prep_data(function_data):
    cvss3_data = []
    node_attributes = []
    node_attributes.append(function_data["clustering_coefficient"])
    node_attributes.append(function_data["distance_to_interface"])
    node_attributes.append(function_data["macke_bug_chain_length"])
    node_attributes.append(function_data["macke_vulnerabilities_found"])
    node_attributes.append(function_data["node_degree"][0])
    node_attributes.append(function_data["node_degree"][1])
    node_attributes.append(function_data["node_path_length"])
    node_attributes.append(function_data["n_pointer_args"])
    node_attributes.append(function_data["function_length"])
    node_attributes.append(function_data["n_blocks"])
    cvss3_data = function_data["cvss3"]
    """
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
            node_attributes.append(value[0])
            node_attributes.append(value[1])
        elif key == 'node_path_length':
            node_attributes.append(value)
        elif key == 'n_pointer_args':
            node_attributes.append(value)
        elif key == 'function_length':
            node_attributes.append(value)
        elif key == 'n_blocks':
            node_attributes.append(value)
    """
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



def evaluate_best_learner(x, y, kf, est, seed):
    best_score = 0

    if y.shape[0]:
        y = y.flatten()

    for train, valid in kf.split(x):

        X_train, X_valid = x[train], x[valid]
        y_train, y_valid = y[train], y[valid]

        #create classifier
        estimator = est.__name__
        # GaussianNB doesnt have class_weight options , so the exception
        if estimator is 'GaussianNB':
            learner = est()
        elif estimator is 'LogisticRegressionCV':
            learner = est(class_weight='balanced', random_state=seed)
        elif estimator is 'RandomForestClassifier':
            learner = est(class_weight='balanced', random_state=seed)
        elif estimator is 'LinearSVC':
            learner = est(class_weight='balanced', random_state=seed)
        else:
            print("I don't understand the classifier name: %s"%(estimator))

        learner.fit(X_train, y_train)

        #prediction = learner.predict(X_valid)
        score = learner.score(X_valid, y_valid)

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
    
    #binarize data for calculating roc auc
    y_bin = label_binarize(Y, y_class)

    n_classes = y_bin.shape[1]

    #split X and Y
    X_train, X_test, y_train, y_test = split_data(X, Y, testdatasize)
    _, _, y_train_bin, y_test_bin = split_data(X, y_bin, testdatasize)

    #roc_auc = roc_one_vs_rest_rf(X_train, X_test, y_bin_train, y_bin_test, est, n_classes)

    best_learner = None
    best_learner_bin = None
    best_acc_score = 0.
    best_roc_score = 0.
    
    for i in range(10):
        seed = random.randint(0, 1000)
        learner = evaluate_best_learner(X_train, y_train, kf, est, seed)
        learner_bin = evaluate_best_learner(X_train, y_train_bin, kf, est, seed)

        prediction = learner.predict(X_test)
        prediction_bin = label_binarize(prediction, y_class)

        acc_score = metrics.accuracy_score(y_test, prediction)
        
        fpr = dict()
        tpr = dict()
        roc_auc = []
        for i in range(len(y_class)):
            try:
                fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], prediction_bin[:, i])
                roc_auc.append(auc(fpr[i], tpr[i]))
            except IndexError:
                #roc_curve(y_test_bin[:, i], prediction_bin[:, i])
                print("Index Error!")
                print(y_test_bin.shape)
                print(prediction_bin.shape)
                print(len(y_class))
                sys.exit()

        roc_auc_score = numpy.average(roc_auc)

        if acc_score>best_acc_score:
            best_acc_score = acc_score
            best_learner = learner

        if roc_auc_score>best_roc_score:
            best_roc_score = roc_auc_score
            best_learner_bin = learner_bin

    return best_acc_score, best_roc_score

# Main
if len(sys.argv) < 2:
    sys.stderr.write('Syntax : python3 %s <node_attributes_directory> {"old-attributes-only"}\n' % sys.argv[0])
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
    files = glob.glob(sys.argv[1]+"/*.json")
    data = []
    prediction_set = []
    structure_data = []
    for file in files:
        with open(os.path.join(file), encoding="utf-8") as data_file:
            try:
                print("Loading: %s"%(file))
                all_functions = json.load(data_file)
            except UnicodeDecodeError:
                print("Problem loading %s"%(file))
            for key, value in all_functions.items():
                if value['faulty'] is True:
                    data.append(value)
                else:
                    prediction_set.append({key: value})

    for function in data:
        prep_data(function)
    
    if len(sys.argv)==3 and sys.argv[2]=="old-attributes-only":
        X_short = []
        for x in X:
            X_short.append(x[:-3])
        X = X_short

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

    # Shuffle all sets
    (X, y_attack_vector, y_attack_complexity, y_privileges_required, y_user_interaction,
            y_scope, y_integrity_impact, y_confidentiality_impact, y_availability_impact) = shuffle(
                    X, y_attack_vector, y_attack_complexity, y_privileges_required, y_user_interaction,
                    y_scope, y_integrity_impact, y_confidentiality_impact, y_availability_impact)


    # TO_DO make a function to generate these classes looking at y
    y_attack_vector_class = numpy.asarray([0, 1, 2, 3])
    y_attack_complexity_class = numpy.asarray([0, 1])
    y_privileges_required_class = numpy.asarray([0, 1, 2])
    y_user_interaction_class = numpy.asarray([0,1])
    y_scope_class = numpy.asarray([0, 1])
    y_confidentiality_impact_class = y_integrity_impact_class = y_availability_impact_class = numpy.asarray([0,1,2])




    
    testsize = 0.25
    kf = KFold(n_splits=3)

    rf_av_score, rf_av_roc_auc = predict_scores(RandomForestClassifier, X, y_attack_vector, testsize, kf,
                                 y_attack_vector_class)
    rf_ac_score , rf_ac_roc_auc = predict_scores(RandomForestClassifier, X, y_attack_complexity, testsize, kf,
                                                 [0])
    rf_pr_score , rf_pr_roc_auc = predict_scores(RandomForestClassifier, X, y_privileges_required, testsize, kf,
                                                 y_privileges_required_class)
    rf_ui_score , rf_ui_roc_auc = predict_scores(RandomForestClassifier, X, y_user_interaction, testsize, kf,
                                                 [0])
    rf_s_score , rf_s_roc_auc = predict_scores(RandomForestClassifier, X, y_scope, testsize, kf, [0])
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
    print("S : %1.2f           %1.2f" %(rf_s_score, rf_s_roc_auc))
    print("CI: %1.2f           %1.2f" % (rf_ci_score, rf_ci_roc_auc))
    print("I : %1.2f           %1.2f" % (rf_ii_score, rf_ii_roc_auc))
    print("AI: %1.2f           %1.2f" % (rf_ai_score, rf_ai_roc_auc))
    

    
    # GaussianNB
    gnb_av_score , gnb_av_roc_auc = predict_scores(GaussianNB, X, y_attack_vector, testsize, kf, y_attack_vector_class)
    gnb_ac_score , gnb_ac_roc_auc = predict_scores(GaussianNB, X, y_attack_complexity, testsize, kf, [0])
    gnb_pr_score , gnb_pr_roc_auc = predict_scores(GaussianNB, X, y_privileges_required, testsize, kf, y_privileges_required_class)
    gnb_ui_score , gnb_ui_roc_auc = predict_scores(GaussianNB, X, y_user_interaction, testsize, kf, [0])
    gnb_ci_score , gnb_ci_roc_auc = predict_scores(GaussianNB, X, y_confidentiality_impact, testsize, kf, y_confidentiality_impact_class)
    gnb_s_score, gnb_s_roc_auc = predict_scores(GaussianNB, X, y_scope, testsize, kf, [0])
    gnb_ii_score , gnb_ii_roc_auc = predict_scores(GaussianNB, X, y_integrity_impact, testsize,kf, y_integrity_impact_class)
    gnb_ai_score , gnb_ai_roc_auc = predict_scores(GaussianNB, X, y_availability_impact, testsize, kf, y_availability_impact_class)

    print("========================================")
    print("   GNB: ACCURACY SCORES AND ROC AUC")
    print("========================================")
    print("AV: %1.2f           %1.2f" % (gnb_av_score, gnb_av_roc_auc))
    print("AC: %1.2f           %1.2f" % (gnb_ac_score, gnb_ac_roc_auc))
    print("P : %1.2f           %1.2f" % (gnb_pr_score, gnb_pr_roc_auc))
    print("UI: %1.2f           %1.2f" % (gnb_ui_score, gnb_ui_roc_auc))
    print("S : %1.2f           %1.2f " %(gnb_s_score, gnb_s_roc_auc))
    print("CI: %1.2f           %1.2f" % (gnb_ci_score, gnb_ci_roc_auc))
    print("I : %1.2f           %1.2f" % (gnb_ii_score, gnb_ii_roc_auc))
    print("AI: %1.2f           %1.2f" % (gnb_ai_score, gnb_ai_roc_auc))
    


    """
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
    lsvc_s_score, lsvc_s_roc_auc = predict_scores(LinearSVC,X, y_scope, testsize, kf, y_scope_class)
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
    print("S : %1.2f           %1.2f " %(lsvc_s_score, lsvc_s_roc_auc))
    print("CI: %1.2f           %1.2f" % (lsvc_ci_score, lsvc_ci_roc_auc))
    print("I : %1.2f           %1.2f" % (lsvc_ii_score, lsvc_ii_roc_auc))
    print("AI: %1.2f           %1.2f" % (lsvc_ai_score, lsvc_ai_roc_auc))
    """

    """
    #Logistic Regression CV
    
    lrcv_av_score, lrcv_av_roc_auc = predict_scores(LogisticRegressionCV, X, y_attack_vector, testsize, kf, y_attack_vector_class)
    lrcv_ac_score, lrcv_ac_roc_auc = predict_scores(LogisticRegressionCV, X, y_attack_complexity, testsize, kf, y_attack_complexity_class)
    #lrcv_pr_score, lrcv_pr_roc_auc = predict_scores(LogisticRegressionCV, X, y_privileges_required, testsize, kf, y_privileges_required_class)
    lrcv_ui_score, lrcv_ui_roc_auc = predict_scores(LogisticRegressionCV, X, y_user_interaction, testsize, kf, y_user_interaction_class)
    lrcv_ci_score, lrcv_ci_roc_auc = predict_scores(LogisticRegressionCV, X, y_confidentiality_impact, testsize, kf, y_confidentiality_impact_class)
    lrcv_s_score, lrcv_s_roc_auc = predict_scores(LogisticRegressionCV, X, y_scope, testsize, kf, y_scope_class)
    lrcv_ii_score, lrcv_ii_roc_auc = predict_scores(LogisticRegressionCV, X, y_integrity_impact, testsize, kf, y_integrity_impact_class)
    lrcv_ai_score, lrcv_ai_roc_auc = predict_scores(LogisticRegressionCV, X, y_availability_impact, testsize, kf, y_availability_impact_class)

    print("========================================")
    print("   LRCV: ACCURACY SCORES AND ROC AUC")
    print("========================================")
    print("AV: %1.2f           " % (lrcv_av_score))
    print("AC: %1.2f           " % (lrcv_ac_score))
    print("P : not predicted           ")# % (lrcv_pr_score))
    print("UI: %1.2f           " % (lrcv_ui_score))
    print("S : %1.2f           " % (lrcv_s_score))
    print("CI: %1.2f           " % (lrcv_ci_score))
    print("I : %1.2f           " % (lrcv_ii_score))
    print("AI: %1.2f           " % (lrcv_ai_score))

    print("Class weights in CVSS3 base scores")
    print("\ny_attack_vector:")
    print(class_weight.compute_class_weight("balanced", y_attack_vector_class, y_attack_vector))
    print("\ny_attack_complexity:")
    print(class_weight.compute_class_weight("balanced", y_attack_complexity_class, y_attack_complexity))
    print("\ny_privileges_required:")
    #print(class_weight.compute_class_weight("balanced", y_privileges_required_class, y_privileges_required))
    print("\ny_user_interaction:")
    print(class_weight.compute_class_weight("balanced", y_user_interaction_class, y_user_interaction))
    print("\ny_confidentiality_impact:")
    print(class_weight.compute_class_weight("balanced", y_confidentiality_impact_class, y_confidentiality_impact))
    print("\ny_scope:")
    print(class_weight.compute_class_weight("balanced", y_scope_class, y_scope))
    print("\ny_integrity_impact:")
    print(class_weight.compute_class_weight("balanced", y_integrity_impact_class, y_integrity_impact))
    print("\ny_availability_impact:")
    print(class_weight.compute_class_weight("balanced", y_availability_impact_class, y_availability_impact))
    """
