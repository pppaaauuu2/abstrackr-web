import sqlalchemy
from sqlalchemy import *
from sqlalchemy.sql import select
from sqlalchemy.sql import and_, or_
import os, pdb, pickle

engine = create_engine("mysql://root:xxxxx@127.0.0.1:3306/abstrackr")
metadata = MetaData(bind=engine)

####
# bind the tables
citations = Table("Citations", metadata, autoload=True)
labels = Table("Labels", metadata, autoload=True)
reviews = Table("Reviews", metadata, autoload=True)
users = Table("user", metadata, autoload=True)
labeled_features = Table("LabelFeatures", metadata, autoload=True)

def get_labels_from_names(review_names):
    r_ids = get_ids_from_names(review_names)
    if len(r_ids) == 0:
        pdb.set_trace()
    return labels_for_review_ids(r_ids)

def get_ids_from_names(review_names):
    s = reviews.select(reviews.c.name.in_(review_names))
    return [review.review_id for review in s.execute()]

def labels_for_review_ids(review_ids):
    #s = labels.select(labels.c.review_id.in_(review_ids))
    #  this selects labels and information about the corresponding
    # labelers.
    s = select([labels, users, citations.c.abstract], \
                        and_(labels.c.reviewer_id == users.c.id,
                             labels.c.review_id.in_(review_ids),
                             citations.c.citation_id == labels.c.study_id),
                        use_labels=True)

    # unroll the result
    return [x for x in s.execute()]


def write_out_labels_for_reviews(review_sets, out_path):  
    # review_sets is a list of lists; each list therein comprises
    # n reviews corresponding to one single review
    # e.g,. [[my_review_1, my_review_2], [a diff review A, a diff review B]]
    abstract_length = lambda x: 0 if x is None else len(x.split(" "))
    all_results = []
    for reviews in review_sets:
        # first fetch the results
        result = get_labels_from_names(reviews)  
        all_results.append(result)

    # first write out the headers
    out_str = ["\t".join(["meta_review_id", "comprising"]+\
                    all_results[0][0].keys()[:-1] + ["abstract_length"])]

    for i, names in enumerate(review_sets):
        for result in all_results[i]:
            cur_str = "\t".join(["%s" % i, "%s" % "-".join(names)]+\
                                [str(x) for x in result.values()[:-1]]+\
                                [str(abstract_length(result['citations_abstract']))])
            out_str.append(cur_str)
    
    # ok, let's dump the result to file
    out_stream = open(out_path, 'w')
    out_stream.write("\n".join(out_str))
    out_stream.close()

def to_disk(review_names, base_dir):
    review_ids = get_ids_from_names(review_names)
    for review_id in review_ids:
        citations_to_disk(review_id, base_dir)
    
    lbls_to_disk(review_ids, base_dir)


def citations_to_disk(review_id, base_dir, \
                fields=["title", "abstract", "keywords", "authors", "journal"]):
    none_to_text= lambda x: "none" if x is None else x

    s = citations.select(citations.c.review_id==review_id)
    citations_for_review = [x for x in s.execute()]

    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    for field in fields:
        field_path = os.path.join(base_dir, field)
        if not os.path.exists(field_path):
            os.mkdir(field_path)

    for citation in citations_for_review:
        citation_id = citation['citation_id']
        
        for field in fields:
            fout = open(os.path.join(base_dir, field, "%s" % citation_id), 'w')
            fout.write(none_to_text(citation[field]))
            fout.close()

def lbls_to_disk(review_ids, base_dir):
    lbl_d = {}
    s = labels.select(labels.c.review_id.in_(review_ids))
    for lbl in s.execute():
        lbl_d[lbl["study_id"]]=lbl["label"]
    
    fout = open(os.path.join(base_dir, "labels.pickle"), 'w')
    pickle.dump(lbl_d, fout)                     
    fout.close()
    
    # also get labeled features
    lbl_feature_d = {}

    s =  labeled_features.select(labeled_features.c.review_id.in_(review_ids))   
    for lbld_feature in s.execute():
        lbl_feature_d[lbld_feature["term"]] = lbld_feature["label"]
    
    fout = open(os.path.join(base_dir, "labeled_features_d.pickle"), 'w')
    pickle.dump(lbl_feature_d, fout)                     
    fout.close()



### 8/4/11
one = ["t-cell ALL 3"]
two = ["CD_Anti-TNF", "anti_tnf_issa"]
three = ["Efficacy-all-database-citations"]
four = ["Lipid 3 Jenny", "Lipid 3 Shana", "Lipds 5 Shana"]
five = ["Prostate 2011 large DB"]
six = ["Serum Free Light Chain CER"]
seven = ["Text_classification_Pubmed"]
eight = ["prostate cancer AS - search for cohorts"]
nine = ["CIN"]
ten = ["IVDx"]
eleven = ["Anemia Biomarkers CER June 2011 1-999", 
          "Anemia Biomarkers CER June 2011 1000-1999",
          "Anemia Biomarkers CER June 2011 2000-2999",
          "Anemia_CER_3000-3999_6-24-2011",
          "Anemia_CER_4000-4999_6-24-2011",
          "Anemia_CER_5000-5722_6-24-2011"]
twelve = ["Lipid frequency of testing-Ethan", 
          "Lipid frequency of testing-Ethan 2",
          "Lipid frequency of testing-Ethan 3"]

def combine_reviews():
    write_out_labels_for_reviews([one, two, three, four, five, six, \
                    seven, eight, nine, ten, eleven, twelve], "twelve2")
                

def all_to_disk():
    #to_disk(one, "T-CELL")
    to_disk(two, "anti-tnf")
    to_disk(three, "efficacy")
    to_disk(four, "lipids")
    to_disk(five, "prostate")
    to_disk(six, "serum")
    to_disk(seven, "text_classification")
    to_disk(eight, "prostate_as")
    to_disk(nine, "CIN")
    to_disk(ten, "IVDx")
    to_disk(eleven, "anemia_biomarkers")
    to_disk(twelve, "lipid_frequency")