from flask import request, jsonify
from flask_cors import cross_origin
from datetime import datetime
import math

def load(app):
    @app.route('/study_sessions', methods=['POST'])
    @cross_origin()
    def create_study_session():
        try:
            data = request.get_json()
            group_id = data.get('group_id')
            study_activity_id = data.get('study_activity_id')

            if not group_id:
                return jsonify({"error": "group_id is required"}), 400
            if not study_activity_id:
                return jsonify({"error": "study_activity_id is required"}), 400

            cursor = app.db.cursor()
            cursor.execute('SELECT id FROM groups WHERE id = ?', (group_id,))
            group = cursor.fetchone()
            if not group:
                return jsonify({"error": "Group not found"}), 404

            cursor.execute('SELECT id FROM study_activities WHERE id = ?', (study_activity_id,))
            study_activity = cursor.fetchone()
            if not study_activity:
                return jsonify({"error": "Study activity not found"}), 404

            cursor.execute('''
                INSERT INTO study_sessions (group_id, study_activity_id, created_at)
                VALUES (?, ?, ?)
            ''', (group_id, study_activity_id, datetime.now()))
            app.db.commit()
            session_id = cursor.lastrowid

            return jsonify({"session_id": session_id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/study-sessions', methods=['GET'])
    @cross_origin()
    def get_study_sessions():
        try:
            cursor = app.db.cursor()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            offset = (page - 1) * per_page

            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM study_sessions ss
                JOIN groups g ON g.id = ss.group_id
                JOIN study_activities sa ON sa.id = ss.study_activity_id
            ''')
            total_count = cursor.fetchone()['count']

            cursor.execute('''
                SELECT 
                    ss.id,
                    ss.group_id,
                    g.name as group_name,
                    sa.id as activity_id,
                    sa.name as activity_name,
                    ss.created_at,
                    COUNT(wri.id) as review_items_count
                FROM study_sessions ss
                JOIN groups g ON g.id = ss.group_id
                JOIN study_activities sa ON sa.id = ss.study_activity_id
                LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
                GROUP BY ss.id
                ORDER BY ss.created_at DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
            sessions = cursor.fetchall()

            return jsonify({
                'items': [{
                    'id': session['id'],
                    'group_id': session['group_id'],
                    'group_name': session['group_name'],
                    'activity_id': session['activity_id'],
                    'activity_name': session['activity_name'],
                    'start_time': session['created_at'],
                    'end_time': session['created_at'],
                    'review_items_count': session['review_items_count']
                } for session in sessions],
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': math.ceil(total_count / per_page)
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/study-sessions/<id>', methods=['GET'])
    @cross_origin()
    def get_study_session(id):
        try:
            cursor = app.db.cursor()
            cursor.execute('''
                SELECT 
                    ss.id,
                    ss.group_id,
                    g.name as group_name,
                    sa.id as activity_id,
                    sa.name as activity_name,
                    ss.created_at,
                    COUNT(wri.id) as review_items_count
                FROM study_sessions ss
                JOIN groups g ON g.id = ss.group_id
                JOIN study_activities sa ON sa.id = ss.study_activity_id
                LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
                WHERE ss.id = ?
                GROUP BY ss.id
            ''', (id,))
            session = cursor.fetchone()
            if not session:
                return jsonify({"error": "Study session not found"}), 404

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            offset = (page - 1) * per_page

            cursor.execute('''
                SELECT 
                    w.*,
                    COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as session_correct_count,
                    COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as session_wrong_count
                FROM words w
                JOIN word_review_items wri ON wri.word_id = w.id
                WHERE wri.study_session_id = ?
                GROUP BY w.id
                ORDER BY w.kanji
                LIMIT ? OFFSET ?
            ''', (id, per_page, offset))
            words = cursor.fetchall()

            cursor.execute('''
                SELECT COUNT(DISTINCT w.id) as count
                FROM words w
                JOIN word_review_items wri ON wri.word_id = w.id
                WHERE wri.study_session_id = ?
            ''', (id,))
            total_count = cursor.fetchone()['count']

            return jsonify({
                'session': {
                    'id': session['id'],
                    'group_id': session['group_id'],
                    'group_name': session['group_name'],
                    'activity_id': session['activity_id'],
                    'activity_name': session['activity_name'],
                    'start_time': session['created_at'],
                    'end_time': session['created_at'],
                    'review_items_count': session['review_items_count']
                },
                'words': [{
                    'id': word['id'],
                    'kanji': word['kanji'],
                    'romaji': word['romaji'],
                    'french': word['french'],
                    'correct_count': word['session_correct_count'],
                    'wrong_count': word['session_wrong_count']
                } for word in words],
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': math.ceil(total_count / per_page)
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/study_sessions/<id>/review', methods=['POST'])
    @cross_origin()
    def log_review(id):
        try:
            cursor = app.db.cursor()
            word_id = request.json.get('word_id')
            correct = request.json.get('correct')
            if word_id is None or correct is None:
                return jsonify({"error": "word_id and correct fields are required"}), 400

            cursor.execute('SELECT id FROM words WHERE id = ?', (word_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Word not found"}), 404

            cursor.execute('SELECT id FROM study_sessions WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Study session not found"}), 404

            cursor.execute('''
                INSERT INTO word_review_items (word_id, correct, study_session_id) VALUES (?, ?, ?)
            ''', (word_id, correct, id))

            cursor.execute('SELECT * FROM word_reviews WHERE word_id = ?', (word_id,))
            review = cursor.fetchone()

            if review:
                if correct:
                    cursor.execute('''
                        UPDATE word_reviews SET correct_count = correct_count + 1, last_reviewed = ? WHERE word_id = ?
                    ''', (datetime.now(), word_id))
                else:
                    cursor.execute('''
                        UPDATE word_reviews SET wrong_count = wrong_count + 1, last_reviewed = ? WHERE word_id = ?
                    ''', (datetime.now(), word_id))
            else:
                cursor.execute('''
                    INSERT INTO word_reviews (word_id, correct_count, wrong_count, last_reviewed)
                    VALUES (?, ?, ?, ?)
                ''', (word_id, 1 if correct else 0, 0 if correct else 1, datetime.now()))

            app.db.commit()
            return jsonify({"message": "Review logged successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/study-sessions/reset', methods=['POST'])
    @cross_origin()
    def reset_study_sessions():
        try:
            cursor = app.db.cursor()
            cursor.execute('DELETE FROM word_review_items')
            cursor.execute('DELETE FROM study_sessions')
            app.db.commit()
            return jsonify({"message": "Study history cleared successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500