CREATE TABLE IF NOT EXISTS
    tournaments (
        id TEXT PRIMARY KEY,
        title TEXT,
        tier INTEGER,
        team_size INTEGER,
        date TEXT,
        is_reward_allowed INTEGER,
        bracket_type TEXT
    );

CREATE TABLE IF NOT EXISTS
    stages (
        id TEXT PRIMARY KEY,
        type TEXT,
        tournament_id TEXT NOT NULL,
        FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
    );

CREATE TABLE IF NOT EXISTS
    stage_groups (
        id TEXT PRIMARY KEY,
        winner_rounds_count INTEGER,
        loser_rounds_count INTEGER,
        teams_count INTEGER,
        order_number INTEGER,
        stage_id TEXT NOT NULL,
        FOREIGN KEY (stage_id) REFERENCES stages (id)
    );

CREATE TABLE IF NOT EXISTS
    teams (
        id TEXT PRIMARY KEY,
        name TEXT,
        has_password INTEGER,
        tournament_id TEXT NOT NULL,
        FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
    );

CREATE TABLE IF NOT EXISTS
    players (
        id TEXT NOT NULL,
        name TEXT,
        battles INTEGER,
        rating INTEGER,
        win_ratio REAL,
        wn8 INTEGER,
        clan_id TEXT,
        team_id TEXT NOT NULL,
        PRIMARY KEY (id, team_id),
        FOREIGN KEY (team_id) REFERENCES teams (id)
    );

CREATE TABLE IF NOT EXISTS
    matches (
        id TEXT PRIMARY KEY,
        map TEXT,
        tournament_id TEXT NOT NULL,
        group_id TEXT NOT NULL,
        team1_id TEXT,
        team2_id TEXT,
        winner_id TEXT,
        FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
        FOREIGN KEY (group_id) REFERENCES stage_groups (id),
        FOREIGN KEY (team1_id) REFERENCES teams (id),
        FOREIGN KEY (team2_id) REFERENCES teams (id),
        FOREIGN KEY (winner_id) REFERENCES teams (id)
    );