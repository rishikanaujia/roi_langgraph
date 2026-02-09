flowchart TD
    Start[User Input: List of Countries] --> ParallelResearch

    subgraph Phase1 [PHASE 1: Initial Ranking System]
        
        subgraph Research [Stage 1: Research Compilation]
            ParallelResearch[Split Countries] --> R1[Research Agent 1]
            ParallelResearch --> R2[Research Agent 2]
            ParallelResearch --> RN[Research Agent N]
            
            R1 --> G1[Gather Research]
            R2 --> G1
            RN --> G1
        end

        G1 --> ParallelPresent

        subgraph Presentation [Stage 2: Expert Presentations]
            ParallelPresent[Assign Experts] --> E1[Expert 1: Build Case]
            ParallelPresent --> E2[Expert 2: Build Case]
            ParallelPresent --> EN[Expert N: Build Case]
            
            E1 --> G2[Gather Presentations]
            E2 --> G2
            EN --> G2
        end

        G2 --> ParallelRank

        subgraph Ranking [Stage 3: Peer Evaluation]
            ParallelRank[Distribute to Peers] --> P1[Peer 1: Score All]
            ParallelRank --> P2[Peer 2: Score All]
            ParallelRank --> P3[Peer 3: Score All]
            
            P1 --> Agg[Aggregate Scores]
            P2 --> Agg
            P3 --> Agg
        end

        Agg --> Generate[Generate Rankings]
        Generate --> Output1[Initial Rankings with Scores]
    end

    Output1 --> Decision{Satisfactory?}
    Decision -->|Yes| End1[Use Initial Rankings]
    Decision -->|No| Phase2Start[Proceed to Phase 2]

    style Phase1 fill:#e1f5e1
    style Research fill:#f0f8ff
    style Presentation fill:#f0f8ff
    style Ranking fill:#f0f8ff