flowchart TD
    Start2[Initial Rankings from Phase 1] --> Config

    subgraph Phase2 [PHASE 2: Hot Seat Refinement]
        
        Config[Configure Hot Seat Rules] --> Round

        subgraph HotSeatRound [Hot Seat Round]
            Round[Identify Bottom Performers] --> Select[Select 2-3 for Hot Seat]
            
            Select --> HS1[Hot Seat 1]
            Select --> HS2[Hot Seat 2]
            
            HS1 --> Challenge
            HS2 --> Challenge
            
            Challenge[Peer Challenge Phase] --> C1[Peer 1: Challenge Points]
            Challenge --> C2[Peer 2: Challenge Points]
            Challenge --> C3[Peer 3: Challenge Points]
            
            C1 --> Defend[Defender Responds]
            C2 --> Defend
            C3 --> Defend
            
            Defend --> Improve[Generate Improvements]
        end

        Improve --> Eval{Improved Defense?}
        
        Eval -->|Yes| Reset[Reset Strikes]
        Eval -->|No| Strike[Add Strike]
        
        Strike --> Check{3 Strikes?}
        Check -->|Yes| Eliminate[Eliminate Country]
        Check -->|No| Continue[Continue]
        
        Reset --> Rerank[Re-Rank All]
        Continue --> Rerank
        Eliminate --> Rerank
        
        Rerank --> Stable{Stable OR Max Rounds?}
        Stable -->|No| Round
        Stable -->|Yes| Output2[Final Rankings]
    end

    Output2 --> Report[Detailed Report with Justifications]

    style Phase2 fill:#ffe1e1
    style HotSeatRound fill:#fff4e1