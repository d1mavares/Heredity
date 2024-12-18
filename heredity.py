import csv
import itertools
import sys
#v0: 3/20/23

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])
    #people = load_data('data/family2.csv')

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    p = {my_list: 1 for my_list in people}
    for person in people:
        # person with 0 genes
        if (person not in one_gene) and (person not in two_genes):
            # Unknown mother and father
            if (people[person]['mother'] is None) and (people[person]['father'] is None):
                p[person] *= PROBS["gene"][0]
            # mother and father both with 0 copies of the gene (00)
            elif (people[person]['mother'] not in one_gene) and (people[person]['mother'] not in two_genes) and (people[person]['father'] not in one_gene) and (people[person]['father'] not in two_genes): 
                p[person] *= (1-PROBS["mutation"])*(1-PROBS["mutation"])
            # mother with one gene and father with 0 genes (or vice versa) (01-10)
            elif ((people[person]['mother'] in one_gene) and ((people[person]['father'] not in two_genes) and (people[person]['father'] not in one_gene))) or ((people[person]['father'] in one_gene) and ((people[person]['mother'] not in two_genes) and (people[person]['mother'] not in one_gene))): 
                p[person] *= .5*(1-PROBS["mutation"])
            # mother with two genes and father with 0 genes (or vice versa) (02-20)
            elif ((people[person]['mother'] in two_genes) and ((people[person]['father'] not in two_genes) and (people[person]['father'] not in one_gene))) or ((people[person]['father'] in two_genes) and ((people[person]['mother'] not in two_genes) and (people[person]['mother'] not in one_gene))): 
                p[person] *= (1-PROBS["mutation"])*PROBS["mutation"]
            # both mother and father with one gene (11)
            elif (people[person]['mother'] in one_gene) and (people[person]['father'] in one_gene): 
                p[person] *= .5*.5
            # mother with one gene and father with 2 genes (or vice versa) (12-21)
            elif ((people[person]['mother'] in one_gene) and (people[person]['father'] in two_genes)) or ((people[person]['mother'] in two_genes) and (people[person]['father'] in one_gene)): 
                p[person] *= .5*PROBS["mutation"]
            # both mother and father with two genes (22)
            elif (people[person]['mother'] in two_genes) and (people[person]['father'] in two_genes): 
                p[person] *= PROBS["mutation"]*PROBS["mutation"]

            # joint condition of having or not the trait           
            if person in have_trait:
                p[person] *= PROBS["trait"][0][True]
            else:
                p[person] *= PROBS["trait"][0][False]

        # person with 1 gene
        elif person in one_gene:
            # Unknown mother and father
            if (people[person]['mother'] is None) and (people[person]['father'] is None):
                p[person] *= PROBS["gene"][1]
            # mother and father both with 0 copies of the gene (00)
            elif (people[person]['mother'] not in one_gene) and (people[person]['mother'] not in two_genes) and (people[person]['father'] not in one_gene) and (people[person]['father'] not in two_genes): 
                p[person] *= (1-PROBS["mutation"])*PROBS["mutation"] + PROBS["mutation"]*(1-PROBS["mutation"])
            # mother with one gene and father with 0 genes (or vice versa) (01-10)
            elif ((people[person]['mother'] in one_gene) and ((people[person]['father'] not in two_genes) and (people[person]['father'] not in one_gene))) or ((people[person]['father'] in one_gene) and ((people[person]['mother'] not in two_genes) and (people[person]['mother'] not in one_gene))): 
                p[person] *= .5
            # mother with two genes and father with 0 genes (or vice versa) (02-20)
            elif ((people[person]['mother'] in two_genes) and ((people[person]['father'] not in two_genes) and (people[person]['father'] not in one_gene))) or ((people[person]['father'] in two_genes) and ((people[person]['mother'] not in two_genes) and (people[person]['mother'] not in one_gene))): 
                p[person] *= (1-PROBS["mutation"])*(1-PROBS["mutation"]) + PROBS["mutation"]*PROBS["mutation"]
            # both mother and father with one gene (11)
            elif (people[person]['mother'] in one_gene) and (people[person]['father'] in one_gene): 
                p[person] *= .5
            # mother with one gene and father with 2 genes (or vice versa) (12-21)
            elif ((people[person]['mother'] in one_gene) and (people[person]['father'] in two_genes)) or ((people[person]['mother'] in two_genes) and (people[person]['father'] in one_gene)): 
                p[person] *= .5
            # both mother and father with two genes (22)
            elif (people[person]['mother'] in two_genes) and (people[person]['father'] in two_genes): 
                p[person] *= (1-PROBS["mutation"])*PROBS["mutation"] + PROBS["mutation"]*(1-PROBS["mutation"])

            # joint condition of having or not the trait
            if person in have_trait:
                p[person] *= PROBS["trait"][1][True]
            else:
                p[person] *= PROBS["trait"][1][False]

    # person with 2 genes
        elif person in two_genes:
            # Unknown mother and father
            if (people[person]['mother'] is None) and (people[person]['father'] is None):
                p[person] *= PROBS["gene"][2]
            # mother and father both with 0 copies of the gene (00)
            elif (people[person]['mother'] not in one_gene) and (people[person]['mother'] not in two_genes) and (people[person]['father'] not in one_gene) and (people[person]['father'] not in two_genes): 
                p[person] *= PROBS["mutation"]*PROBS["mutation"]
            # mother with one gene and father with 0 genes (or vice versa) (01-10)
            elif ((people[person]['mother'] in one_gene) and ((people[person]['father'] not in two_genes) and (people[person]['father'] not in one_gene))) or ((people[person]['father'] in one_gene) and ((people[person]['mother'] not in two_genes) and (people[person]['mother'] not in one_gene))): 
                p[person] *= .5*PROBS["mutation"]
            # mother with two genes and father with 0 genes (or vice versa) (02-20)
            elif ((people[person]['mother'] in two_genes) and ((people[person]['father'] not in two_genes) and (people[person]['father'] not in one_gene))) or ((people[person]['father'] in two_genes) and ((people[person]['mother'] not in two_genes) and (people[person]['mother'] not in one_gene))): 
                p[person] *= (1-PROBS["mutation"])*PROBS["mutation"]
            # both mother and father with one gene (11)
            elif (people[person]['mother'] in one_gene) and (people[person]['father'] in one_gene): 
                p[person] *= .5*.5
            # mother with one gene and father with 2 genes (or vice versa) (12-21)
            elif ((people[person]['mother'] in one_gene) and (people[person]['father'] in two_genes)) or ((people[person]['mother'] in two_genes) and (people[person]['father'] in one_gene)): 
                p[person] *= .5*(1-PROBS["mutation"])
            # both mother and father with two genes (22)
            elif (people[person]['mother'] in two_genes) and (people[person]['father'] in two_genes): 
                p[person] *= (1-PROBS["mutation"])*(1-PROBS["mutation"])

            # joint condition of having or not the trait
            if person in have_trait:
                p[person] *= PROBS["trait"][2][True]
            else:
                p[person] *= PROBS["trait"][2][False]
    p2 = 1
    for person in p:
        p2 *= p[person]
    return p2


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    for person in probabilities:
        # person with 0 genes
        if (person not in one_gene) and (person not in two_genes):
            probabilities[person]['gene'][0] += p
        # person with 1 gene
        elif person in one_gene:
            probabilities[person]['gene'][1] += p
        # person with 2 genes
        elif person in two_genes:
            probabilities[person]['gene'][2] += p

        # having or not the trait           
        if person in have_trait:
            probabilities[person]['trait'][True] += p
        else:
            probabilities[person]['trait'][False] += p

#    raise NotImplementedError


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    for person in probabilities:
        A = sum(probabilities[person]['gene'].values())
        B = sum(probabilities[person]['trait'].values())
        for g in probabilities[person]['gene']:
            probabilities[person]['gene'][g] /= A
        for t in probabilities[person]['trait']:
            probabilities[person]['trait'][t] /= B
#    raise NotImplementedError


if __name__ == "__main__":
    main()
