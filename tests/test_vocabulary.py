from vmodel_contracts import (ARTIFACT_LABELS, CONCEPT_OF_OPERATIONS,
                              STAGE_LABELS, ArtifactName, PipelineStage)


def test_conops_vocabulary_is_one_canonical_spelling():
    assert PipelineStage.CONOPS.value == "conops"
    assert STAGE_LABELS[PipelineStage.CONOPS] == CONCEPT_OF_OPERATIONS == "Concept of Operations"
    assert ArtifactName.CONOPS.value == "conops.json"
    assert ARTIFACT_LABELS[ArtifactName.CONOPS] == CONCEPT_OF_OPERATIONS


def test_stage_and_artifact_machine_names_are_unique():
    assert len({x.value for x in PipelineStage}) == len(PipelineStage)
    assert len({x.value for x in ArtifactName}) == len(ArtifactName)
