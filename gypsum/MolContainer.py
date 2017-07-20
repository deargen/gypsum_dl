import sys
import gypsum.Utils as Utils
import gypsum.ChemUtils as ChemUtils
import gypsum.MyMol as MyMol

try:
    from molvs import standardize_smiles as ssmiles
except:
    Utils.log("You need to install molvs and its dependencies.")
    sys.exit(0)

try:
    from rdkit import Chem
except:
    Utils.log("You need to install rdkit and its dependencies.")
    sys.exit(0)


class MolContainer:
    """
    The molecucle container class. It stores all the molecules (tautomers,
    etc.) associated with a single input SMILES entry.
    """

    def __init__(self, smiles, name, index, properties):
        """The constructor for this class.

        :param [str] smiles: A list of SMILES strings.

        :param [str] name: The name of the molecule.

        :param int index: The index of this MolContainer in the main
                          MolContainer list.
        :param {dict} properties: A dictionary of properties from the sdf.
        """

        # Set some variables on the contnr level (not the MyMolecule level)
        self.contnr_idx = index
        self.orig_smi = smiles
        self.orig_smi_deslt = smiles  # initial assumption
        self.mols = []
        #self.smiles_to_pH = {}
        self.name = name
        self.properties = properties
        self.mol_orig_smi = MyMol.MyMol(smiles, name)
        self.frgs = ""  # For caching.

        # Save the original canonical smiles
        self.orig_smi_canonical = self.mol_orig_smi.smiles()

        # Get the number of nonaromatic rings
        self.num_nonaro_rngs = len(self.mol_orig_smi.m_num_nonaro_rngs())

        # Get the number of chiral centers, assigned or not
        self.num_specif_chiral_cntrs = len(
            self.mol_orig_smi.chiral_cntrs_only_asignd()
        )

        # Get the non-acidic carbon-hydrogen footprint.
        self.carbon_hydrogen_count = self.mol_orig_smi.carb_hyd_cnt()

    def mol_with_smiles_is_in_container(self, smiles):
        """
        Checks whether or not a given smiles string is already in this
        container.

        :param str smiles: The smiles string to check.

        :returns: True if it is present, otherwise a new MyMol.MyMol object
                  corresponding to that smiles.
        :rtype: :class:`str` ???
        """

        # Checks all the mols in this container to see if a given smiles is
        # already present. Returns a new MyMol object if it isn't, True
        # otherwise.

        # First, get the set of all cannonical smiles
        # TODO: Probably shouldn't be generating this on the fly every time
        # you use it!
        can_smi_in_this_container = set([m.smiles() for m in self.mols])

        # Get this new smiles in cannonical form
        amol = MyMol.MyMol(smiles)
        if amol.smiles() in can_smi_in_this_container:
            return True
        else:
            return amol

    def add_smiles(self, smiles):
        """
        Adds smiles strings to this container. SMILES are always isomeric and
        always unique (canonical).

        :param str|[str] smiles: A list of SMILES strings. If it's a string,
                         it is converted into a list.
        """

        if isinstance(smiles, str):  # smiles must be array of strs
            smiles = [smiles]

        # Keep only the mols with smiles that are not already present.
        for s in smiles:
            result = self.mol_with_smiles_is_in_container(s)
            if result != True:
                # Much of the contnr info should be passed to each
                # molecule, too, for convenience.
                result.name = self.name
                result.name = self.orig_smi
                result.orig_smi_canonical = self.orig_smi_canonical
                result.orig_smi_deslt = self.orig_smi_deslt
                result.contnr_idx = self.contnr_idx

                self.mols.append(result)

    def add_mol(self, mol):
        """Adds a molecule to this container. Does NOT check for uniqueness.

        :param MyMol.MyMol mol: The MyMol.MyMol object to add.
        """

        self.mols.append(mol)

    def all_smiles(self):
        """
        Gets a list of all the noh canonical smiles in this container.

        :returns: a [str], the canonical, noh smiles string.
        :rtype: :class:`str` ???
        """
        smiles = []
        for m in self.mols:
            if m.rdkit_mol is not None:
                smiles.append(m.smiles(True))

        return smiles

    def get_frags_of_orig_smi(self):
        """
        Gets a list of the fragments found in the original smiles string
        passed to this container.

        :returns: a list of the fragments, as rdkit.Mol objects.
        :rtype: :class:`str` ???
        """

        if self.frgs != "":
            return self.frgs

        frags = self.mol_orig_smi.get_frags_of_orig_smi()
        self.frgs = frags
        return frags

    def update_orig_smi(self, orig_smi):
        """
        Updates the orig_smi string. 

        :param str orig_smi: The replacement smiles string.
        """

        # Update the MolContainer object
        self.orig_smi = orig_smi
        self.orig_smi_deslt = orig_smi
        self.mol_orig_smi = MyMol.MyMol(self.orig_smi, self.name)
        self.frgs = ""
        self.orig_smi_canonical = self.mol_orig_smi.smiles()
        self.num_nonaro_rngs = len(self.mol_orig_smi.m_num_nonaro_rngs())
        self.num_specif_chiral_cntrs = len(
            self.mol_orig_smi.chiral_cntrs_only_asignd()
        )

        # None of the mols derived to date, if present, are accurate.
        self.mols = []

    def add_container_properties(self):
        """
        
        """
        for mol in self.mols:
            mol.mol_props.update(self.properties)
            mol.setAllRDKitMolProps()
