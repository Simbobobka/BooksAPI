INSERT INTO genres (name) VALUES
    ('Fiction'),
    ('Non-Fiction'),
    ('Science'),
    ('History'),
    ('Biography'),
    ('Fantasy'),
    ('Mystery'),
    ('Poetry'),
    ('Romance'),
    ('Thriller')
ON CONFLICT (name) DO NOTHING;
