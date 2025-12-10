"""
Tests for Agent Metadata

Tests Phase 1 agent metadata functionality including:
- Factory functions
- Validation
- Metadata creation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.agent_metadata import (
    AgentMetadata,
    AgentCapability,
    AgentFramework,
    create_expert_metadata,
    create_peer_ranker_metadata,
    validate_phase1_agent,
    RESEARCH_LOADER_METADATA,
    EXPERT_AGENT_METADATA,
    PEER_RANKER_METADATA,
    AGGREGATOR_METADATA
)


def test_expert_metadata_creation():
    """Test expert agent metadata factory."""
    print("\n" + "=" * 70)
    print("TEST: Expert Metadata Creation")
    print("=" * 70)

    usa_expert = create_expert_metadata("USA", expert_id=1)

    print(f"✅ Expert Agent: {usa_expert.agent_id}")
    print(f"   Name: {usa_expert.name}")
    print(f"   Description: {usa_expert.description}")
    print(f"   Framework: {usa_expert.framework.value}")
    print(f"   Capabilities: {[c.value for c in usa_expert.capabilities]}")
    print(f"   Business Unit: {usa_expert.business_unit}")
    print(f"   Required Inputs: {usa_expert.required_inputs}")
    print(f"   Output Keys: {usa_expert.output_keys}")
    print(f"   Tags: {usa_expert.tags}")
    print(f"   Config: {usa_expert.config}")

    # Assertions
    assert usa_expert.agent_id == "expert_usa_1"
    assert "USA" in usa_expert.name
    assert AgentCapability.EXPERT_PRESENTATION in usa_expert.capabilities
    assert usa_expert.framework == AgentFramework.LANGCHAIN
    assert "country_research" in usa_expert.required_inputs
    assert "expert_presentations" in usa_expert.output_keys
    assert usa_expert.config["assigned_country"] == "USA"

    print("\n✅ Expert metadata creation: PASSED")


def test_peer_ranker_metadata_creation():
    """Test peer ranker metadata factory."""
    print("\n" + "=" * 70)
    print("TEST: Peer Ranker Metadata Creation")
    print("=" * 70)

    peer_1 = create_peer_ranker_metadata(ranker_id=1)

    print(f"✅ Peer Ranker: {peer_1.agent_id}")
    print(f"   Name: {peer_1.name}")
    print(f"   Description: {peer_1.description}")
    print(f"   Framework: {peer_1.framework.value}")
    print(f"   Capabilities: {[c.value for c in peer_1.capabilities]}")
    print(f"   Business Unit: {peer_1.business_unit}")
    print(f"   Required Inputs: {peer_1.required_inputs}")
    print(f"   Output Keys: {peer_1.output_keys}")
    print(f"   Tags: {peer_1.tags}")
    print(f"   Config: {peer_1.config}")

    # Assertions
    assert peer_1.agent_id == "peer_ranker_1"
    assert "Peer Ranker #1" in peer_1.name
    assert AgentCapability.PEER_RANKING in peer_1.capabilities
    assert peer_1.framework == AgentFramework.LANGCHAIN
    assert "expert_presentations" in peer_1.required_inputs
    assert "peer_rankings" in peer_1.output_keys
    assert peer_1.config["ranker_id"] == 1

    print("\n✅ Peer ranker metadata creation: PASSED")


def test_multiple_countries():
    """Test creating experts for multiple countries."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Country Experts")
    print("=" * 70)

    countries = ["USA", "IND", "CHN", "BRA", "DEU"]
    experts = []

    for country in countries:
        expert = create_expert_metadata(country, expert_id=1)
        experts.append(expert)
        print(f"✅ Created expert for {country}: {expert.agent_id}")

    # Assertions
    assert len(experts) == len(countries)
    assert all(AgentCapability.EXPERT_PRESENTATION in e.capabilities for e in experts)
    assert len(set(e.agent_id for e in experts)) == len(experts)  # All unique IDs

    print(f"\n✅ Created {len(experts)} unique expert agents: PASSED")


def test_multiple_peer_rankers():
    """Test creating multiple peer rankers."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Peer Rankers")
    print("=" * 70)

    num_peers = 5
    peers = []

    for i in range(1, num_peers + 1):
        peer = create_peer_ranker_metadata(ranker_id=i)
        peers.append(peer)
        print(f"✅ Created peer ranker #{i}: {peer.agent_id}")

    # Assertions
    assert len(peers) == num_peers
    assert all(AgentCapability.PEER_RANKING in p.capabilities for p in peers)
    assert len(set(p.agent_id for p in peers)) == num_peers  # All unique IDs

    print(f"\n✅ Created {num_peers} unique peer rankers: PASSED")


def test_validation():
    """Test agent validation."""
    print("\n" + "=" * 70)
    print("TEST: Agent Validation")
    print("=" * 70)

    # Test valid agents
    usa_expert = create_expert_metadata("USA", expert_id=1)
    peer_1 = create_peer_ranker_metadata(ranker_id=1)

    print(f"Validating USA Expert: {validate_phase1_agent(usa_expert)}")
    print(f"Validating Peer Ranker: {validate_phase1_agent(peer_1)}")
    print(f"Validating Research Loader: {validate_phase1_agent(RESEARCH_LOADER_METADATA)}")
    print(f"Validating Aggregator: {validate_phase1_agent(AGGREGATOR_METADATA)}")

    assert validate_phase1_agent(usa_expert) == True
    assert validate_phase1_agent(peer_1) == True
    assert validate_phase1_agent(RESEARCH_LOADER_METADATA) == True
    assert validate_phase1_agent(AGGREGATOR_METADATA) == True

    # Test invalid agent (no Phase 1 capabilities)
    invalid_agent = AgentMetadata(
        agent_id="invalid",
        name="Invalid Agent",
        description="Has no Phase 1 capabilities",
        framework=AgentFramework.CUSTOM,
        capabilities=[AgentCapability.VERIFICATION],  # Not a Phase 1 capability
        business_unit="tests",
        contact="tests@tests.com",
        required_inputs=["input"],
        output_keys=["output"]
    )

    print(f"Validating Invalid Agent: {validate_phase1_agent(invalid_agent)}")
    assert validate_phase1_agent(invalid_agent) == False

    print("\n✅ Validation tests: PASSED")


def test_predefined_metadata():
    """Test predefined metadata templates."""
    print("\n" + "=" * 70)
    print("TEST: Predefined Metadata Templates")
    print("=" * 70)

    templates = [
        ("Research Loader", RESEARCH_LOADER_METADATA),
        ("Expert Agent", EXPERT_AGENT_METADATA),
        ("Peer Ranker", PEER_RANKER_METADATA),
        ("Aggregator", AGGREGATOR_METADATA)
    ]

    for name, metadata in templates:
        print(f"\n{name}:")
        print(f"  Agent ID: {metadata.agent_id}")
        print(f"  Capabilities: {[c.value for c in metadata.capabilities]}")
        print(f"  Framework: {metadata.framework.value}")
        print(f"  Inputs: {metadata.required_inputs}")
        print(f"  Outputs: {metadata.output_keys}")

        # Validate
        is_valid = validate_phase1_agent(metadata)
        print(f"  Valid: {is_valid}")
        assert is_valid == True

    print("\n✅ Predefined metadata templates: PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL AGENT METADATA TESTS")
    print("=" * 70)

    tests = [
        test_expert_metadata_creation,
        test_peer_ranker_metadata_creation,
        test_multiple_countries,
        test_multiple_peer_rankers,
        test_validation,
        test_predefined_metadata
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} tests(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)